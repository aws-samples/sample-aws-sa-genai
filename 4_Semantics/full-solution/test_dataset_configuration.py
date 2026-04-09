#!/usr/bin/env python3
"""
Unit tests for the Dataset Configuration section of snowflake_to_quicksight.py.

Tests cover:
  - list_quicksight_datasets       (pagination)
  - _dataset_uses_datasource       (physical-table inspection)
  - filter_datasets_by_datasource  (datasource filter)
  - _search_datasets               (case-insensitive substring search)
  - _pick_dataset_from_list        (interactive list + search)
  - select_dataset_mode            (create / update / sub-menu)
  - create_or_replace_dataset
  - update_existing_dataset
"""

import sys
import unittest
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, __file__.rsplit('/', 1)[0])

from snowflake_to_quicksight import (
    list_quicksight_datasets,
    _dataset_uses_datasource,
    filter_datasets_by_datasource,
    _search_datasets,
    _pick_dataset_from_list,
    select_dataset_mode,
    create_or_replace_dataset,
    update_existing_dataset,
)

DS_ARN = 'arn:aws:quicksight:us-east-1:123:datasource/sf-ds'
ACCOUNT = '123456789012'

SAMPLE_DATASETS = [
    {'DataSetId': 'ds-001', 'Name': 'Movie Analytics',  'ImportMode': 'SPICE'},
    {'DataSetId': 'ds-002', 'Name': 'Sales Dashboard',  'ImportMode': 'DIRECT_QUERY'},
    {'DataSetId': 'ds-003', 'Name': 'Movie Insights',   'ImportMode': 'SPICE'},
]


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_qs(datasets=None, *, raise_not_found_on_delete=True):
    """Return a minimal mock QuickSight client."""
    qs = MagicMock()
    qs.list_data_sets.return_value = {'DataSetSummaries': datasets or []}

    not_found = type('ResourceNotFoundException', (Exception,), {})
    qs.exceptions.ResourceNotFoundException = not_found
    if raise_not_found_on_delete:
        qs.delete_data_set.side_effect = not_found("not found")
    else:
        qs.delete_data_set.return_value = {}

    qs.create_data_set.return_value = {'DataSetId': 'test-dataset-id', 'Status': 201}
    qs.update_data_set.return_value = {'DataSetId': 'existing-dataset-id', 'Status': 200}
    return qs


def _describe_side_effect(datasource_arn):
    """
    Return a describe_data_set side-effect function.
    ds-001 and ds-003 use DS_ARN; ds-002 does not.
    """
    def _side_effect(AwsAccountId, DataSetId):
        if DataSetId in ('ds-001', 'ds-003'):
            arn = datasource_arn
        else:
            arn = 'arn:aws:quicksight:us-east-1:123:datasource/other'
        return {
            'DataSet': {
                'PhysicalTableMap': {
                    't1': {'RelationalTable': {'DataSourceArn': arn}}
                }
            }
        }
    return _side_effect


# ── list_quicksight_datasets ──────────────────────────────────────────────────

class TestListQuickSightDatasets(unittest.TestCase):

    def test_returns_empty_list_when_none(self):
        qs = _make_qs(datasets=[])
        self.assertEqual(list_quicksight_datasets(qs, ACCOUNT), [])

    def test_returns_all_datasets_single_page(self):
        qs = _make_qs(datasets=SAMPLE_DATASETS)
        result = list_quicksight_datasets(qs, ACCOUNT)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['DataSetId'], 'ds-001')

    def test_paginates_multiple_pages(self):
        page1 = {'DataSetSummaries': [SAMPLE_DATASETS[0]], 'NextToken': 'tok1'}
        page2 = {'DataSetSummaries': [SAMPLE_DATASETS[1]]}
        qs = MagicMock()
        qs.list_data_sets.side_effect = [page1, page2]

        result = list_quicksight_datasets(qs, ACCOUNT)
        self.assertEqual(len(result), 2)
        self.assertEqual(qs.list_data_sets.call_count, 2)
        # second call must carry the token
        second_call_kwargs = qs.list_data_sets.call_args_list[1][1]
        self.assertEqual(second_call_kwargs.get('NextToken'), 'tok1')


# ── _dataset_uses_datasource ──────────────────────────────────────────────────

class TestDatasetUsesDatasource(unittest.TestCase):

    def _make_describe(self, datasource_arn):
        return lambda AwsAccountId, DataSetId: {
            'DataSet': {
                'PhysicalTableMap': {
                    't1': {'RelationalTable': {'DataSourceArn': datasource_arn}}
                }
            }
        }

    def test_returns_true_when_matching(self):
        qs = MagicMock()
        qs.describe_data_set.side_effect = self._make_describe(DS_ARN)
        self.assertTrue(_dataset_uses_datasource(qs, ACCOUNT, 'ds-001', DS_ARN))

    def test_returns_false_when_not_matching(self):
        qs = MagicMock()
        qs.describe_data_set.side_effect = self._make_describe('arn:aws:qs:::datasource/other')
        self.assertFalse(_dataset_uses_datasource(qs, ACCOUNT, 'ds-002', DS_ARN))

    def test_returns_false_on_api_error(self):
        qs = MagicMock()
        qs.describe_data_set.side_effect = Exception("Access denied")
        self.assertFalse(_dataset_uses_datasource(qs, ACCOUNT, 'ds-x', DS_ARN))

    def test_checks_custom_sql_datasource(self):
        qs = MagicMock()
        qs.describe_data_set.return_value = {
            'DataSet': {
                'PhysicalTableMap': {
                    't1': {'CustomSql': {'DataSourceArn': DS_ARN}}
                }
            }
        }
        self.assertTrue(_dataset_uses_datasource(qs, ACCOUNT, 'ds-001', DS_ARN))


# ── filter_datasets_by_datasource ─────────────────────────────────────────────

class TestFilterDatasetsByDatasource(unittest.TestCase):

    def test_returns_only_matching_datasets(self):
        qs = MagicMock()
        qs.describe_data_set.side_effect = _describe_side_effect(DS_ARN)

        result = filter_datasets_by_datasource(qs, ACCOUNT, SAMPLE_DATASETS, DS_ARN)
        ids = [ds['DataSetId'] for ds in result]
        self.assertIn('ds-001', ids)
        self.assertIn('ds-003', ids)
        self.assertNotIn('ds-002', ids)

    def test_returns_empty_when_no_match(self):
        qs = MagicMock()
        qs.describe_data_set.side_effect = _describe_side_effect('arn:aws:qs:::datasource/x')
        result = filter_datasets_by_datasource(qs, ACCOUNT, SAMPLE_DATASETS, DS_ARN)
        self.assertEqual(result, [])


# ── _search_datasets ──────────────────────────────────────────────────────────

class TestSearchDatasets(unittest.TestCase):

    def test_matches_name_case_insensitive(self):
        result = _search_datasets(SAMPLE_DATASETS, 'movie')
        self.assertEqual(len(result), 2)

    def test_matches_dataset_id(self):
        result = _search_datasets(SAMPLE_DATASETS, 'ds-002')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['DataSetId'], 'ds-002')

    def test_no_match_returns_empty(self):
        self.assertEqual(_search_datasets(SAMPLE_DATASETS, 'zzz_nonexistent'), [])

    def test_empty_term_matches_all(self):
        self.assertEqual(len(_search_datasets(SAMPLE_DATASETS, '')), 3)


# ── _pick_dataset_from_list ───────────────────────────────────────────────────

class TestPickDatasetFromList(unittest.TestCase):

    def _make_qs_with_filter(self):
        qs = _make_qs(datasets=SAMPLE_DATASETS)
        qs.describe_data_set.side_effect = _describe_side_effect(DS_ARN)
        return qs

    @patch('builtins.input', side_effect=['1', ''])   # pick first, keep name
    def test_picks_first_matching_dataset(self, _):
        qs = self._make_qs_with_filter()
        result = _pick_dataset_from_list(qs, ACCOUNT, DS_ARN)
        self.assertIsNotNone(result)
        dataset_id, dataset_name = result
        self.assertEqual(dataset_id, 'ds-001')
        self.assertEqual(dataset_name, 'Movie Analytics')

    @patch('builtins.input', side_effect=['B'])
    def test_returns_none_on_back(self, _):
        qs = self._make_qs_with_filter()
        self.assertIsNone(_pick_dataset_from_list(qs, ACCOUNT, DS_ARN))

    @patch('builtins.input', side_effect=['insight', '1', ''])  # search then pick
    def test_search_then_pick(self, _):
        qs = self._make_qs_with_filter()
        result = _pick_dataset_from_list(qs, ACCOUNT, DS_ARN)
        self.assertIsNotNone(result)
        dataset_id, _ = result
        self.assertEqual(dataset_id, 'ds-003')   # 'Movie Insights' is the only insight match

    @patch('builtins.input', side_effect=['zzz', '1', ''])  # bad search → full list → pick
    def test_bad_search_falls_back_to_full_list(self, _):
        qs = self._make_qs_with_filter()
        result = _pick_dataset_from_list(qs, ACCOUNT, DS_ARN)
        self.assertIsNotNone(result)

    @patch('builtins.input', side_effect=['99', '1', ''])  # out-of-range → retry → pick
    def test_out_of_range_number_retries(self, _):
        qs = self._make_qs_with_filter()
        result = _pick_dataset_from_list(qs, ACCOUNT, DS_ARN)
        self.assertIsNotNone(result)

    @patch('builtins.input', side_effect=['1', 'Renamed Movie'])  # pick and rename
    def test_allows_renaming_on_pick(self, _):
        qs = self._make_qs_with_filter()
        _, dataset_name = _pick_dataset_from_list(qs, ACCOUNT, DS_ARN)
        self.assertEqual(dataset_name, 'Renamed Movie')

    def test_returns_none_when_no_datasets_for_datasource(self):
        qs = _make_qs(datasets=SAMPLE_DATASETS)
        qs.describe_data_set.return_value = {
            'DataSet': {'PhysicalTableMap': {
                't1': {'RelationalTable': {'DataSourceArn': 'arn:aws:qs:::datasource/other'}}
            }}
        }
        result = _pick_dataset_from_list(qs, ACCOUNT, DS_ARN)
        self.assertIsNone(result)


# ── select_dataset_mode ───────────────────────────────────────────────────────

class TestSelectDatasetModeCreate(unittest.TestCase):

    @patch('builtins.input', side_effect=['1', 'new-dataset', 'New Dataset Name'])
    def test_create_explicit_values(self, _):
        qs = _make_qs()
        mode, ds_id, ds_name = select_dataset_mode(qs, ACCOUNT, DS_ARN)
        self.assertEqual(mode, 'create')
        self.assertEqual(ds_id, 'new-dataset')
        self.assertEqual(ds_name, 'New Dataset Name')

    @patch('builtins.input', side_effect=['1', '', ''])   # empty → defaults
    def test_create_uses_defaults(self, _):
        qs = _make_qs()
        mode, ds_id, ds_name = select_dataset_mode(qs, ACCOUNT)
        self.assertEqual(mode, 'create')
        self.assertEqual(ds_id, 'movie-analytics-dataset')
        self.assertEqual(ds_name, 'Movie Analytics Dataset')

    @patch('builtins.input', side_effect=['bad', '1', '', ''])   # invalid → create
    def test_invalid_top_level_retries(self, _):
        qs = _make_qs()
        mode, _, _ = select_dataset_mode(qs, ACCOUNT)
        self.assertEqual(mode, 'create')


class TestSelectDatasetModeUpdatePickList(unittest.TestCase):
    """Update → [A] pick from list."""

    def _qs(self):
        qs = _make_qs(datasets=SAMPLE_DATASETS)
        qs.describe_data_set.side_effect = _describe_side_effect(DS_ARN)
        return qs

    @patch('builtins.input', side_effect=['2', 'A', '1', ''])
    def test_update_pick_first(self, _):
        mode, ds_id, ds_name = select_dataset_mode(self._qs(), ACCOUNT, DS_ARN)
        self.assertEqual(mode, 'update')
        self.assertEqual(ds_id, 'ds-001')

    @patch('builtins.input', side_effect=['2', 'A', '2', 'Renamed'])
    def test_update_pick_second_with_rename(self, _):
        mode, ds_id, ds_name = select_dataset_mode(self._qs(), ACCOUNT, DS_ARN)
        self.assertEqual(mode, 'update')
        self.assertEqual(ds_id, 'ds-003')   # filtered: ds-001, ds-003
        self.assertEqual(ds_name, 'Renamed')

    @patch('builtins.input', side_effect=['2', 'A', 'B', '2', 'A', '1', ''])
    def test_back_from_list_returns_to_sub_menu(self, _):
        """Pressing B inside the list re-shows the A/B sub-menu."""
        mode, ds_id, _ = select_dataset_mode(self._qs(), ACCOUNT, DS_ARN)
        self.assertEqual(mode, 'update')
        self.assertEqual(ds_id, 'ds-001')


class TestSelectDatasetModeUpdateTypeId(unittest.TestCase):
    """Update → [B] type dataset ID directly."""

    @patch('builtins.input', side_effect=['2', 'B', 'my-custom-id', 'My Custom Name'])
    def test_update_type_in_id(self, _):
        mode, ds_id, ds_name = select_dataset_mode(_make_qs(), ACCOUNT, DS_ARN)
        self.assertEqual(mode, 'update')
        self.assertEqual(ds_id, 'my-custom-id')
        self.assertEqual(ds_name, 'My Custom Name')

    @patch('builtins.input', side_effect=['2', 'B', '', 'B', 'valid-id', ''])  # empty → re-ask sub → valid
    def test_update_type_in_empty_retries(self, _):
        mode, ds_id, _ = select_dataset_mode(_make_qs(), ACCOUNT, DS_ARN)
        self.assertEqual(mode, 'update')
        self.assertEqual(ds_id, 'valid-id')

    @patch('builtins.input', side_effect=['2', 'X', 'B', 'typed-id', ''])  # bad sub then B
    def test_invalid_sub_choice_retries(self, _):
        mode, ds_id, _ = select_dataset_mode(_make_qs(), ACCOUNT, DS_ARN)
        self.assertEqual(mode, 'update')
        self.assertEqual(ds_id, 'typed-id')


# ── create_or_replace_dataset ─────────────────────────────────────────────────

class TestCreateOrReplaceDataset(unittest.TestCase):

    def test_creates_when_not_exists(self):
        qs = _make_qs(raise_not_found_on_delete=True)
        schema = {'DataSetId': 'test-dataset-id', 'Name': 'Test'}
        with patch('time.sleep'):
            result = create_or_replace_dataset(qs, ACCOUNT, schema)
        qs.create_data_set.assert_called_once()
        self.assertEqual(result['DataSetId'], 'test-dataset-id')

    def test_deletes_existing_then_creates(self):
        qs = _make_qs(raise_not_found_on_delete=False)
        schema = {'DataSetId': 'test-dataset-id', 'Name': 'Test'}
        with patch('time.sleep'):
            create_or_replace_dataset(qs, ACCOUNT, schema)
        qs.delete_data_set.assert_called_once_with(
            AwsAccountId=ACCOUNT, DataSetId='test-dataset-id'
        )
        qs.create_data_set.assert_called_once()


# ── update_existing_dataset ───────────────────────────────────────────────────

class TestUpdateExistingDataset(unittest.TestCase):

    def test_calls_update_data_set(self):
        qs = _make_qs()
        schema = {'DataSetId': 'existing-dataset-id', 'Name': 'Updated Name'}
        result = update_existing_dataset(qs, ACCOUNT, schema)
        qs.update_data_set.assert_called_once_with(AwsAccountId=ACCOUNT, **schema)
        self.assertEqual(result['DataSetId'], 'existing-dataset-id')

    def test_does_not_call_delete(self):
        qs = _make_qs()
        update_existing_dataset(qs, ACCOUNT, {'DataSetId': 'existing-dataset-id', 'Name': 'X'})
        qs.delete_data_set.assert_not_called()

    def test_does_not_call_create(self):
        qs = _make_qs()
        update_existing_dataset(qs, ACCOUNT, {'DataSetId': 'existing-dataset-id', 'Name': 'X'})
        qs.create_data_set.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
