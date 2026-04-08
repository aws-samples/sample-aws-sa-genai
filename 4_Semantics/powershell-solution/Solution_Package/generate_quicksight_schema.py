#!/usr/bin/env python3
"""
Snowflake DDL to QuickSight Dataset Schema Generator

This script reads a Snowflake Semantic View DDL from a CSV file and generates a complete
QuickSight dataset schema with physical tables, logical tables with joins, column renames,
type casts, calculated fields, and descriptions.

Fully generic — works with any Snowflake Semantic View DDL structure:
  - Tables with or without explicit aliases
  - Tables with or without primary keys / unique constraints
  - Dimensions where the expression is a bare column name (no TABLE. prefix)
  - Facts where the right-hand side has no table prefix
  - Any number of tables and relationships (arbitrary join graph, BFS-ordered)
  - Duplicate column names across tables (auto-prefixed with table alias)
  - Synonyms on dimensions used as QuickSight column descriptions
  - Metrics converted to QuickSight calculated fields
"""

import csv
import re
import json
import uuid
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple


# ── Helpers ───────────────────────────────────────────────────────────────────

def snowflake_type_to_qs(data_type: str, numeric_scale: Optional[int]) -> str:
    """
    Convert a Snowflake INFORMATION_SCHEMA DATA_TYPE to a QuickSight column type.
    """
    t = (data_type or '').upper()
    if t in ('INT', 'INTEGER', 'BIGINT', 'SMALLINT', 'TINYINT', 'BYTEINT'):
        return 'INTEGER'
    if t in ('NUMBER', 'DECIMAL', 'NUMERIC'):
        if numeric_scale is not None and numeric_scale == 0:
            return 'INTEGER'
        return 'DECIMAL'
    if t in ('FLOAT', 'FLOAT4', 'FLOAT8', 'DOUBLE', 'DOUBLE PRECISION', 'REAL'):
        return 'DECIMAL'
    if t == 'TIME' or t.startswith('TIME_'):
        return 'SKIP'   # Sentinel: exclude this column from InputColumns
    if t.startswith('DATE') or t.startswith('TIMESTAMP'):
        return 'DATETIME'
    return 'STRING'


def _extract_section(ddl: str, keyword: str, terminators: List[str]) -> Optional[str]:
    """
    Extract the content of a named DDL section, e.g. 'tables', 'dimensions'.
    Stops at the first matching terminator keyword or end-of-string.
    Uses brace-matching to correctly handle nested parentheses.
    """
    kw_pat = rf'\b{re.escape(keyword)}\s*\('
    m = re.search(kw_pat, ddl, re.IGNORECASE)
    if not m:
        return None

    depth = 0
    start = m.end() - 1  # position of '('
    i = start
    while i < len(ddl):
        if ddl[i] == '(':
            depth += 1
        elif ddl[i] == ')':
            depth -= 1
            if depth == 0:
                return ddl[start + 1:i]
        i += 1
    return ddl[start + 1:]


def _infer_qs_type(col_name: str, expression: str) -> str:
    """
    Infer a QuickSight column type from the exposed column name and expression.
    """
    cu, eu = col_name.upper(), expression.upper()
    if any(f in eu for f in ['YEAR(', 'MONTH(', 'DAY(']):
        return 'INTEGER'
    if 'TIMESTAMP' in cu or ('DATE' in cu and 'UPDATE' not in cu and 'CANDIDATE' not in cu):
        return 'DATETIME'
    if 'CONCAT(' in eu:
        return 'STRING'
    if any(re.search(rf'(^|_){w}($|_)', cu) for w in ['YEAR', 'MONTH', 'DAY']):
        return 'INTEGER'
    if cu.endswith('ID') and 'CONCAT(' not in eu:
        return 'INTEGER'
    return 'STRING'


# ── Parser ────────────────────────────────────────────────────────────────────

class SnowflakeDDLParser:
    """
    Parse Snowflake Semantic View DDL into structured dicts.

    DDL format variations handled
    ──────────────────────────────
    Tables
      • ALIAS as DB.SCHEMA.TABLE primary key (PK)           ← MOVIES-style
      • DB.SCHEMA.TABLE primary key (PK) unique (U) ...     ← no alias
      • DB.SCHEMA.TABLE                                      ← no PK at all

    Dimensions
      • TABLE.EXPOSED_NAME as TABLE.PHYSICAL_COL            ← rename + table prefix on both sides
      • TABLE.EXPOSED_NAME as PHYSICAL_COL_OR_EXPR          ← physical col has no table prefix

    Facts
      • TABLE.EXPOSED_NAME as TABLE.PHYSICAL_COL            ← MOVIES-style
      • TABLE.PHYSICAL_COL as PLAIN_ALIAS                   ← BMW-style (right = plain alias)
    """

    def __init__(self):
        self.ddl_content = ""
        self.tables: List[Dict] = []
        self.relationships: List[Dict] = []
        self.facts: List[Dict] = []
        self.dimensions: List[Dict] = []
        self.metrics: List[Dict] = []

    # ── Loaders ───────────────────────────────────────────────────────────────

    def load_from_string(self, ddl: str) -> 'SnowflakeDDLParser':
        self.ddl_content = ddl
        return self

    def load_from_csv(self, csv_path: str) -> 'SnowflakeDDLParser':
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if len(row) > 1:
                    self.ddl_content = row[1]
                    break
        return self

    # ── Section parsers ───────────────────────────────────────────────────────

    def parse_tables(self) -> List[Dict]:
        content = _extract_section(self.ddl_content, 'tables', ['relationships'])
        if not content:
            return self.tables

        for raw_line in content.split('\n'):
            line = raw_line.strip().rstrip(',').strip()
            if not line or line.startswith('--'):
                continue

            m_alias = re.match(r'(\w+)\s+as\s+([\w.]+)', line, re.IGNORECASE)
            if m_alias:
                alias     = m_alias.group(1)
                full_name = m_alias.group(2)
            else:
                m_bare = re.match(r'([\w.]+)', line)
                if not m_bare:
                    continue
                full_name = m_bare.group(1)
                parts     = full_name.split('.')
                alias     = parts[-1]

            parts      = full_name.split('.')
            database   = parts[0]              if len(parts) >= 3 else ''
            schema     = parts[-2]             if len(parts) >= 2 else 'PUBLIC'
            table_name = parts[-1]

            pk_m         = re.search(r'primary\s+key\s*\(([^)]+)\)', line, re.IGNORECASE)
            primary_keys = [k.strip() for k in pk_m.group(1).split(',')] if pk_m else []

            self.tables.append({
                'alias':        alias,
                'full_name':    full_name,
                'database':     database,
                'schema':       schema,
                'table_name':   table_name,
                'primary_keys': primary_keys,
            })

        return self.tables

    def parse_relationships(self) -> List[Dict]:
        content = _extract_section(self.ddl_content, 'relationships', ['facts', 'dimensions'])
        if not content:
            return self.relationships

        pattern = r'(\w+)\s+as\s+(\w+)\s*\(([^)]+)\)\s+references\s+(\w+)\s*\(([^)]+)\)'
        for m in re.finditer(pattern, content, re.IGNORECASE):
            self.relationships.append({
                'name':        m.group(1),
                'from_table':  m.group(2),
                'from_column': m.group(3).strip(),
                'to_table':    m.group(4),
                'to_column':   m.group(5).strip(),
            })

        return self.relationships

    def parse_facts(self) -> List[Dict]:
        content = _extract_section(self.ddl_content, 'facts', ['dimensions'])
        if not content:
            return self.facts

        for m in re.finditer(r'([\w.]+)\s+as\s+([\w.]+)', content):
            left  = m.group(1)
            right = m.group(2)

            if '.' in left:
                alias_table, alias_col = left.split('.', 1)
            else:
                alias_table, alias_col = None, left

            if '.' in right:
                phys_table, phys_col = right.split('.', 1)
            else:
                phys_table = alias_table
                phys_col   = right

            self.facts.append({
                'alias_table': alias_table,
                'alias_col':   alias_col.upper(),
                'phys_table':  phys_table,
                'phys_col':    phys_col.upper(),
                'type':        'DECIMAL',
            })

        return self.facts

    def parse_dimensions(self) -> List[Dict]:
        content = _extract_section(
            self.ddl_content, 'dimensions',
            ['metrics', 'with', ';']
        )
        if not content:
            return self.dimensions

        for raw_line in content.split('\n'):
            line = raw_line.strip()
            if not line or line.startswith('--'):
                continue

            m = re.match(
                r'([\w.]+)\s+as\s+(.+?)(?:\s+with\s+synonyms|\s+comment\s*=|,?\s*$)',
                line
            )
            if not m:
                continue

            alias      = m.group(1)
            expression = m.group(2).strip().rstrip(',').strip()

            if '.' in alias:
                table_alias, renamed_col = alias.split('.', 1)
            else:
                table_alias = renamed_col = alias

            comment_m = re.search(r"comment\s*=\s*'([^']+)'", line)
            comment   = comment_m.group(1) if comment_m else ''

            syn_m    = re.search(r"with\s+synonyms\s*=\s*\(([^)]+)\)", line, re.IGNORECASE)
            synonyms = []
            if syn_m:
                synonyms = [
                    s.strip().strip("'\"")
                    for s in syn_m.group(1).split(',')
                    if s.strip().strip("'\"")
                ]

            physical_columns = [
                {'table': t, 'column': c.upper()}
                for t, c in re.findall(r'(\w+)\.(\w+)', expression)
            ]

            is_calculated = '(' in expression and any(
                fn in expression.upper()
                for fn in ['CONCAT', 'YEAR', 'MONTH', 'DAY', 'CAST', 'SUBSTRING', 'COALESCE', 'IFF']
            )

            if not physical_columns and not is_calculated and table_alias:
                bare = expression.rstrip(',').strip()
                if re.match(r'^\w+$', bare):
                    physical_columns = [{'table': table_alias, 'column': bare.upper()}]

            self.dimensions.append({
                'alias':            alias,
                'table_alias':      table_alias,
                'renamed_column':   renamed_col.upper(),
                'expression':       expression,
                'physical_columns': physical_columns,
                'is_calculated':    is_calculated,
                'type':             _infer_qs_type(renamed_col, expression),
                'comment':          comment,
                'synonyms':         synonyms,
            })

        return self.dimensions

    def parse_metrics(self) -> List[Dict]:
        content = _extract_section(
            self.ddl_content, 'metrics',
            ['with', ';', 'comment']
        )
        if not content:
            return self.metrics

        pattern = r'([\w.]+)\s+as\s+(.+?)\s+with\s+synonyms'
        for m in re.findall(pattern, content, re.DOTALL):
            alias      = m[0].strip()
            expression = m[1].strip()

            comment = ''
            for line in content.split('\n'):
                if alias in line and ' as ' in line:
                    cm = re.search(r"comment\s*=\s*'([^']+)'", line)
                    comment = cm.group(1) if cm else ''
                    break

            self.metrics.append({
                'alias':      alias,
                'expression': expression,
                'type':       'INTEGER' if 'COUNT' in expression.upper() else 'DECIMAL',
                'comment':    comment,
            })

        return self.metrics

    def parse_all(self) -> Dict:
        if not self.ddl_content:
            raise ValueError("No DDL loaded. Call load_from_string() or load_from_csv() first.")
        self.tables        = []
        self.relationships = []
        self.facts         = []
        self.dimensions    = []
        self.metrics       = []
        self.parse_tables()
        self.parse_relationships()
        self.parse_facts()
        self.parse_dimensions()
        self.parse_metrics()
        return {
            'tables':        self.tables,
            'relationships': self.relationships,
            'facts':         self.facts,
            'dimensions':    self.dimensions,
            'metrics':       self.metrics,
        }


# ── Schema Generator ──────────────────────────────────────────────────────────

class QuickSightSchemaGenerator:
    """
    Generate a complete QuickSight dataset schema (SPICE) from parsed DDL.

    Column naming strategy
    ──────────────────────
    If the same logical column name is exposed by more than one table, the
    column is prefixed with the table alias to avoid post-join collisions:
        COUNTRY exposed by DAPP + OFCON  →  DAPP_COUNTRY, OFCON_COUNTRY

    Columns unique across all tables keep their plain name.

    Join ordering
    ─────────────
    Tables are joined in BFS order starting from the table that appears as
    'from_table' most often but never as 'to_table' (a pure source / fact
    table). This produces a valid left-deep join tree for any DAG topology.
    """

    def __init__(self, parsed_ddl: Dict):
        self.parsed_ddl       = parsed_ddl
        self.physical_table_map: Dict = {}
        self.logical_table_map:  Dict = {}
        self._rename_map:    Dict[str, Dict[str, str]] = {}
        self._final_names:   Dict[str, Set[str]] = {}
        self._col_db:        Dict[str, str] = {}
        self._skipped:       Set[Tuple[str, str]] = set()

    # ── Column naming ─────────────────────────────────────────────────────────

    def _build_rename_map(self) -> Dict[str, Dict[str, str]]:
        """Determine the final QuickSight name for every physical column."""
        exposure: Dict[str, List[str]] = {}

        for dim in self.parsed_ddl['dimensions']:
            if dim['is_calculated'] or not dim['table_alias']:
                continue
            lname = dim['renamed_column']
            exposure.setdefault(lname, [])
            if dim['table_alias'] not in exposure[lname]:
                exposure[lname].append(dim['table_alias'])

        for fact in self.parsed_ddl['facts']:
            lname = fact['alias_col']
            exposure.setdefault(lname, [])
            ta = fact['alias_table'] or fact['phys_table'] or ''
            if ta and ta not in exposure[lname]:
                exposure[lname].append(ta)

        rename_map: Dict[str, Dict[str, str]] = {}
        skipped = self._skipped

        for dim in self.parsed_ddl['dimensions']:
            if dim['is_calculated'] or not dim['table_alias']:
                continue
            ta       = dim['table_alias']
            lname    = dim['renamed_column']
            phys_col = (
                dim['physical_columns'][0]['column']
                if dim['physical_columns'] else lname
            )
            if (ta.upper(), phys_col.upper()) in skipped:
                continue
            final = f"{ta}_{lname}" if len(exposure.get(lname, [])) > 1 else lname
            rename_map.setdefault(ta, {})[phys_col] = final

        for fact in self.parsed_ddl['facts']:
            ta       = fact['phys_table'] or fact['alias_table'] or ''
            phys_col = fact['phys_col']
            lname    = fact['alias_col']
            final    = f"{ta}_{lname}" if len(exposure.get(lname, [])) > 1 else lname
            if not ta:
                continue
            rename_map.setdefault(ta, {})
            if phys_col != final:
                rename_map[ta][phys_col] = final

        self._rename_map = rename_map

        # Build logical→final lookup for metric resolution
        self._logical_to_final: Dict[str, Dict[str, str]] = {}
        for dim in self.parsed_ddl['dimensions']:
            if dim['is_calculated'] or not dim['table_alias']:
                continue
            ta      = dim['table_alias']
            exposed = dim['renamed_column']
            phys    = (dim['physical_columns'][0]['column'] if dim['physical_columns'] else exposed)
            final   = rename_map.get(ta, {}).get(phys, exposed)
            self._logical_to_final.setdefault(ta, {})[exposed.upper()] = final

        for fact in self.parsed_ddl['facts']:
            ta      = fact['alias_table'] or fact['phys_table'] or ''
            exposed = fact['alias_col']
            phys    = fact['phys_col']
            final   = rename_map.get(fact['phys_table'] or '', {}).get(phys, exposed)
            if ta:
                self._logical_to_final.setdefault(ta, {})[exposed.upper()] = final

        self._final_names = {}
        for dim in self.parsed_ddl['dimensions']:
            if dim['is_calculated'] or not dim['table_alias']:
                continue
            ta    = dim['table_alias']
            phys  = dim['physical_columns'][0]['column'] if dim['physical_columns'] else dim['renamed_column']
            fname = rename_map.get(ta, {}).get(phys, dim['renamed_column'])
            self._final_names.setdefault(ta, set()).add(fname)

        for fact in self.parsed_ddl['facts']:
            ta    = fact['phys_table'] or fact['alias_table'] or ''
            phys  = fact['phys_col']
            fname = rename_map.get(ta, {}).get(phys, fact['alias_col'])
            if ta:
                self._final_names.setdefault(ta, set()).add(fname)

        return rename_map

    def _final_col(self, table_alias: str, phys_col: str) -> str:
        """Return the QuickSight final name for a physical column in a table."""
        return self._rename_map.get(table_alias, {}).get(phys_col.upper(), phys_col.upper())

    # ── BFS join ordering ─────────────────────────────────────────────────────

    def _bfs_join_order(self) -> List[str]:
        """Return table aliases in BFS order suitable for sequential LEFT joins."""
        tables = self.parsed_ddl['tables']
        rels   = self.parsed_ddl['relationships']

        if not rels:
            return [t['alias'] for t in tables]

        all_aliases = {t['alias'] for t in tables}

        adj: Dict[str, Set[str]] = {ta: set() for ta in all_aliases}
        for rel in rels:
            ft, tt = rel['from_table'], rel['to_table']
            if ft in adj: adj[ft].add(tt)
            if tt in adj: adj[tt].add(ft)

        from_count: Dict[str, int] = {}
        for rel in rels:
            from_count[rel['from_table']] = from_count.get(rel['from_table'], 0) + 1

        to_set   = {rel['to_table'] for rel in rels}
        pure_src = set(from_count) - to_set

        if pure_src:
            start = max(pure_src, key=lambda x: from_count.get(x, 0))
        elif from_count:
            start = max(from_count, key=from_count.get)
        else:
            start = tables[0]['alias']

        visited: List[str] = []
        seen:    Set[str]  = set()
        queue = [start]
        while queue:
            curr = queue.pop(0)
            if curr in seen:
                continue
            seen.add(curr)
            visited.append(curr)
            for nb in sorted(adj.get(curr, [])):
                if nb not in seen:
                    queue.append(nb)

        for t in tables:
            if t['alias'] not in seen:
                visited.append(t['alias'])

        return visited

    # ── Physical table map ────────────────────────────────────────────────────

    def generate_physical_table_map(
        self,
        datasource_arn: str,
        database: str,
        column_type_overrides: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> Dict:
        """Build PhysicalTableMap: one RelationalTable entry per Snowflake table."""
        table_cols: Dict[str, Dict[str, str]] = {}

        for dim in self.parsed_ddl['dimensions']:
            for pc in dim['physical_columns']:
                ta, col = pc['table'], pc['column']
                table_cols.setdefault(ta, {})
                if col not in table_cols[ta]:
                    table_cols[ta][col] = _infer_qs_type(dim['renamed_column'], dim['expression'])

        for fact in self.parsed_ddl['facts']:
            ta, col = fact['phys_table'], fact['phys_col']
            if not ta:
                continue
            table_cols.setdefault(ta, {})
            if col not in table_cols[ta]:
                table_cols[ta][col] = fact['type']

        alias_db      = {t['alias']: t.get('database', database) for t in self.parsed_ddl['tables']}
        self._col_db  = alias_db
        self._skipped = set()

        for table in self.parsed_ddl['tables']:
            table_id = table['alias'].lower().replace('_', '-')
            ta       = table['alias']
            db       = alias_db.get(ta, database) or database

            overrides = {}
            if column_type_overrides:
                overrides = column_type_overrides.get(ta.upper(), {})

            input_columns = []
            for col_name, col_type in sorted(table_cols.get(ta, {}).items()):
                col_type = overrides.get(col_name.upper(), col_type)
                if col_type == 'SKIP':
                    self._skipped.add((ta.upper(), col_name.upper()))
                    continue
                col_def = {'Name': col_name, 'Type': col_type}
                if col_type == 'DECIMAL':
                    col_def['SubType'] = 'FLOAT'
                input_columns.append(col_def)

            if not input_columns:
                input_columns = [
                    {'Name': pk.upper(), 'Type': 'INTEGER'}
                    for pk in table.get('primary_keys', [])
                ]

            entry: Dict = {
                'RelationalTable': {
                    'DataSourceArn': datasource_arn,
                    'Catalog':       db,
                    'Schema':        table['schema'],
                    'Name':          table['table_name'],
                    'InputColumns':  input_columns,
                }
            }
            if not entry['RelationalTable']['Catalog']:
                del entry['RelationalTable']['Catalog']

            self.physical_table_map[table_id] = entry

        return self.physical_table_map

    # ── Logical table map ─────────────────────────────────────────────────────

    def generate_logical_table_map(self) -> Dict:
        """Build LogicalTableMap with renames, joins, calculated fields and descriptions."""
        self._build_rename_map()

        tables_list = self.parsed_ddl['tables']
        table_ids   = {t['alias']: t['alias'].lower().replace('_', '-') for t in tables_list}

        # 1. One logical node per physical table (with rename transforms)
        for table in tables_list:
            ta      = table['alias']
            node_id = table_ids[ta]

            transforms = []
            renames    = self._rename_map.get(ta, {})

            for phys_col, final_name in renames.items():
                if phys_col == final_name:
                    continue
                transforms.append({
                    'RenameColumnOperation': {
                        'ColumnName':    phys_col,
                        'NewColumnName': final_name,
                    }
                })

            self.logical_table_map[node_id] = {
                'Alias':  table['table_name'],
                'Source': {'PhysicalTableId': node_id},
            }
            if transforms:
                self.logical_table_map[node_id]['DataTransforms'] = transforms

        # 2. Build join tree in BFS order
        join_order = self._bfs_join_order()

        rel_map: Dict[Tuple[str, str], Tuple[str, str]] = {}
        for rel in self.parsed_ddl['relationships']:
            ft, tt = rel['from_table'], rel['to_table']
            fc, tc = rel['from_column'].upper(), rel['to_column'].upper()
            rel_map[(ft, tt)] = (fc, tc)
            rel_map[(tt, ft)] = (tc, fc)

        current_id  = table_ids.get(join_order[0], join_order[0].lower())
        accumulated: Set[str] = {join_order[0]}

        for i, next_alias in enumerate(join_order[1:], start=1):
            left_col = right_col = None
            for acc in accumulated:
                pair = rel_map.get((acc, next_alias)) or rel_map.get((next_alias, acc))
                if pair:
                    acc_phys, new_phys = pair
                    left_col  = self._final_col(acc, acc_phys)
                    right_col = self._final_col(next_alias, new_phys)
                    break

            if left_col is None:
                continue

            accumulated.add(next_alias)
            right_id = table_ids.get(next_alias, next_alias.lower())
            join_id  = f'join-{i}'

            self.logical_table_map[join_id] = {
                'Alias':  join_id,
                'Source': {
                    'JoinInstruction': {
                        'LeftOperand':  current_id,
                        'RightOperand': right_id,
                        'Type':         'OUTER',
                        'OnClause':     f'{{{left_col}}} = {{{right_col}}}',
                    }
                },
            }
            current_id = join_id

        # 3. Final transforms on the last join node (or base table)
        transforms = []

        # 3a. Calculated dimensions (CONCAT, YEAR, MONTH, DAY, …)
        for dim in self.parsed_ddl['dimensions']:
            if not dim['is_calculated']:
                continue
            col_name = dim['renamed_column']
            expr     = dim['expression']

            expr = expr.replace('CONCAT(', 'concat(')
            date_handled = False
            for fn, fmt in [('YEAR(', "'YYYY'"), ('MONTH(', "'MM'"), ('DAY(', "'DD'")]:
                if fn in expr.upper():
                    m = re.search(rf'{re.escape(fn)}([\w.]+)\)', expr, re.IGNORECASE)
                    if m:
                        col_ref = m.group(1)
                        for pc in dim['physical_columns']:
                            final = self._final_col(pc['table'], pc['column'])
                            col_ref = re.sub(
                                rf'\b{pc["table"]}\.{pc["column"]}\b',
                                f'{{{final}}}', col_ref, flags=re.IGNORECASE
                            )
                        expr = f"extract({fmt},{col_ref})"
                    date_handled = True
                    break

            if not date_handled:
                for pc in dim['physical_columns']:
                    final = self._final_col(pc['table'], pc['column'])
                    expr  = re.sub(
                        rf'\b{pc["table"]}\.{pc["column"]}\b',
                        f'{{{final}}}', expr, flags=re.IGNORECASE
                    )

            transforms.append({
                'CreateColumnsOperation': {
                    'Columns': [{'ColumnName': col_name, 'ColumnId': str(uuid.uuid4()), 'Expression': expr}]
                }
            })

        # 3b. Metrics as calculated fields
        for metric in self.parsed_ddl['metrics']:
            col_name = metric['alias'].replace('.', '_').upper()
            expr     = metric['expression']

            for other in self.parsed_ddl['metrics']:
                if other['alias'] != metric['alias']:
                    other_name = other['alias'].replace('.', '_').upper()
                    expr = re.sub(
                        rf'\b{re.escape(other["alias"])}\b',
                        f'{{{other_name}}}', expr, flags=re.IGNORECASE
                    )

            for sf, qs in [
                ('COUNT(DISTINCT', 'distinct_count('),
                ('COUNT(',         'count('),
                ('AVG(',           'avg('),
                ('SUM(',           'sum('),
                ('MAX(',           'max('),
                ('MIN(',           'min('),
            ]:
                expr = expr.replace(sf, qs)

            for t, c in re.findall(r'(\w+)\.(\w+)', expr):
                final = (
                    self._logical_to_final.get(t, {}).get(c.upper())
                    or self._final_col(t, c.upper())
                )
                expr = expr.replace(f'{t}.{c}', f'{{{final}}}')

            transforms.append({
                'CreateColumnsOperation': {
                    'Columns': [{'ColumnName': col_name, 'ColumnId': str(uuid.uuid4()), 'Expression': expr}]
                }
            })

        # 3c. Column descriptions: comment takes priority, then synonyms
        tag_dict: Dict[str, Dict] = {}
        for dim in self.parsed_ddl['dimensions']:
            col_name   = dim['renamed_column']
            phys_cols  = dim['physical_columns']
            ta         = dim['table_alias']
            final_name = (
                self._final_col(ta, phys_cols[0]['column']) if phys_cols
                else col_name
            )

            description = dim.get('comment', '')
            if not description and dim.get('synonyms'):
                description = 'Synonyms: ' + ', '.join(dim['synonyms'])

            if description:
                tag_dict[final_name] = {
                    'TagColumnOperation': {
                        'ColumnName': final_name,
                        'Tags': [{'ColumnDescription': {'Text': description}}],
                    }
                }

        for metric in self.parsed_ddl['metrics']:
            col_name    = metric['alias'].replace('.', '_').upper()
            description = metric.get('comment', '')
            if description:
                tag_dict[col_name] = {
                    'TagColumnOperation': {
                        'ColumnName': col_name,
                        'Tags': [{'ColumnDescription': {'Text': description}}],
                    }
                }

        transforms.extend(tag_dict.values())

        # 3d. ProjectOperation — keep only semantically defined columns
        projected: List[str] = []
        seen_p: Set[str]     = set()

        def _add(name: str):
            if name not in seen_p:
                seen_p.add(name)
                projected.append(name)

        skipped = self._skipped

        for dim in self.parsed_ddl['dimensions']:
            if not dim['is_calculated'] and dim['table_alias'] and dim['physical_columns']:
                pc = dim['physical_columns'][0]
                if (dim['table_alias'].upper(), pc['column'].upper()) in skipped:
                    continue
                _add(self._final_col(dim['table_alias'], pc['column']))
            elif dim['is_calculated']:
                _add(dim['renamed_column'])

        for fact in self.parsed_ddl['facts']:
            if fact['phys_table']:
                _add(self._final_col(fact['phys_table'], fact['phys_col']))

        for metric in self.parsed_ddl['metrics']:
            _add(metric['alias'].replace('.', '_').upper())

        for calc_dim in self.parsed_ddl['dimensions']:
            if calc_dim['is_calculated']:
                _add(calc_dim['renamed_column'])

        if projected:
            transforms.append({'ProjectOperation': {'ProjectedColumns': projected}})

        if transforms:
            self.logical_table_map[current_id]['DataTransforms'] = (
                self.logical_table_map[current_id].get('DataTransforms', []) + transforms
            )

        return self.logical_table_map

    # ── Entry point ───────────────────────────────────────────────────────────

    def generate_complete_schema(
        self,
        datasource_arn: str,
        database: str,
        dataset_id: str,
        dataset_name: str,
        column_type_overrides: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> Dict:
        """Return the full QuickSight SPICE dataset schema dict."""
        self.physical_table_map = {}
        self.logical_table_map  = {}
        self._skipped           = set()
        self.generate_physical_table_map(datasource_arn, database, column_type_overrides)
        self.generate_logical_table_map()
        return {
            'DataSetId':   dataset_id,
            'Name':        dataset_name,
            'PhysicalTableMap': self.physical_table_map,
            'LogicalTableMap':  self.logical_table_map,
            'ImportMode':  'SPICE',
            'DataSetUsageConfiguration': {
                'DisableUseAsDirectQuerySource': False,
                'DisableUseAsImportedSource':    False,
            },
        }


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate complete QuickSight dataset schema from Snowflake DDL CSV'
    )
    parser.add_argument('--csv-path',       default='SF_DDL.csv',
                        help='Path to Snowflake DDL CSV file (default: SF_DDL.csv)')
    parser.add_argument('--datasource-arn', required=True,
                        help='QuickSight data source ARN')
    parser.add_argument('--database',       default='MOVIES',
                        help='Snowflake database name (default: MOVIES)')
    parser.add_argument('--dataset-id',     default='movie-analytics-dataset',
                        help='QuickSight dataset ID (default: movie-analytics-dataset)')
    parser.add_argument('--dataset-name',   default='Movie Analytics Dataset',
                        help='QuickSight dataset display name')
    parser.add_argument('--output',         default='quicksight_schema_complete.json',
                        help='Output JSON file path (default: quicksight_schema_complete.json)')
    args = parser.parse_args()

    print(f"Parsing Snowflake DDL from: {args.csv_path}")
    ddl_parser = SnowflakeDDLParser()
    ddl_parser.load_from_csv(args.csv_path)
    parsed = ddl_parser.parse_all()

    print(f"Found {len(parsed['tables'])} tables")
    print(f"Found {len(parsed['relationships'])} relationships")
    print(f"Found {len(parsed['dimensions'])} dimensions")
    print(f"Found {len(parsed['facts'])} facts")
    print(f"Found {len(parsed['metrics'])} metrics")

    print("\nGenerating complete QuickSight dataset schema...")
    generator = QuickSightSchemaGenerator(parsed)
    schema = generator.generate_complete_schema(
        datasource_arn=args.datasource_arn,
        database=args.database,
        dataset_id=args.dataset_id,
        dataset_name=args.dataset_name,
    )

    with open(args.output, 'w') as f:
        json.dump(schema, f, indent=2)

    table_names = ', '.join(t['table_name'] for t in parsed['tables'])
    calc_dims   = [d['renamed_column'] for d in parsed['dimensions'] if d['is_calculated']]
    calc_fields = calc_dims + [m['alias'].replace('.', '_').upper() for m in parsed['metrics']]

    print(f"\nComplete schema saved to: {args.output}")
    print("\nThis schema includes:")
    print(f"  ✓ All {len(parsed['tables'])} physical tables ({table_names})")
    if parsed['relationships']:
        print(f"  ✓ Logical tables with {len(parsed['relationships'])} join(s)")
    print(f"  ✓ Column renames based on DDL aliases")
    print(f"  ✓ Type casts (IDs to STRING)")
    if calc_fields:
        print(f"  ✓ Calculated fields ({', '.join(calc_fields[:3])}{'...' if len(calc_fields) > 3 else ''})")
    print(f"  ✓ Column descriptions from DDL comments")


if __name__ == '__main__':
    main()
