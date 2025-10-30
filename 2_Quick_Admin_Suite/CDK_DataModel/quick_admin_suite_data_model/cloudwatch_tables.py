from aws_cdk import aws_glue as glue

def create_cloudwatch_tables(stack, admin_console_db):
    """Create CloudWatch metrics tables"""
    
    # CloudWatch QuickSight Dataset Table
    cw_qs_ds_table = glue.CfnTable(
        stack, "CwQsDsTable",
        catalog_id=stack.account,
        database_name=admin_console_db.ref,
        table_input=glue.CfnTable.TableInputProperty(
            name=f"cw_qs_ds_{stack.account}",
            description="CloudWatch Metrics Stream data for QuickSight",
            parameters={
                "classification": "json",
                "partition_filtering.enabled": "true"
            },
            storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                columns=[
                    glue.CfnTable.ColumnProperty(name="metric_stream_name", type="string", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="account_id", type="string", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="region", type="string", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="namespace", type="string", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="metric_name", type="string", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="dimensions", type="struct<DatasetId:string>", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="timestamp", type="bigint", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="value", type="struct<max:double,min:double,sum:double,count:double>", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="unit", type="string", comment="from deserializer")
                ],
                input_format="org.apache.hadoop.mapred.TextInputFormat",
                output_format="org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
                serde_info=glue.CfnTable.SerdeInfoProperty(
                    serialization_library="org.openx.data.jsonserde.JsonSerDe",
                    parameters={
                        "paths": "account_id,dimensions,metric_name,metric_stream_name,namespace,region,timestamp,unit,value"
                    }
                ),
                location=f"s3://cw-qs-ds-{stack.account}/"
            ),
            partition_keys=[
                glue.CfnTable.ColumnProperty(name="partition_0", type="string"),
                glue.CfnTable.ColumnProperty(name="partition_1", type="string"),
                glue.CfnTable.ColumnProperty(name="partition_2", type="string"),
                glue.CfnTable.ColumnProperty(name="partition_3", type="string")
            ],
            table_type="EXTERNAL_TABLE"
        )
    )

    # CloudWatch QuickSight Dashboard Visual Table
    cw_qs_dash_visual_table = glue.CfnTable(
        stack, "CwQsDashVisualTable",
        catalog_id=stack.account,
        database_name=admin_console_db.ref,
        table_input=glue.CfnTable.TableInputProperty(
            name=f"cw_qs_dash_visual_{stack.account}",
            description="CloudWatch Metrics Stream data for QuickSight Dashboard Visual",
            parameters={
                "classification": "json",
                "partition_filtering.enabled": "true"
            },
            storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                columns=[
                    glue.CfnTable.ColumnProperty(name="metric_stream_name", type="string", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="account_id", type="string", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="region", type="string", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="namespace", type="string", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="metric_name", type="string", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="dimensions", type="struct<DashboardId:string,SheetId:string,VisualId:string>", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="timestamp", type="bigint", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="value", type="struct<max:double,min:double,sum:double,count:double>", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="unit", type="string", comment="from deserializer")
                ],
                input_format="org.apache.hadoop.mapred.TextInputFormat",
                output_format="org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
                serde_info=glue.CfnTable.SerdeInfoProperty(
                    serialization_library="org.openx.data.jsonserde.JsonSerDe",
                    parameters={
                        "paths": "account_id,dimensions,metric_name,metric_stream_name,namespace,region,timestamp,unit,value"
                    }
                ),
                location=f"s3://cw-qs-dash-visual-{stack.account}/"
            ),
            partition_keys=[
                glue.CfnTable.ColumnProperty(name="partition_0", type="string"),
                glue.CfnTable.ColumnProperty(name="partition_1", type="string"),
                glue.CfnTable.ColumnProperty(name="partition_2", type="string"),
                glue.CfnTable.ColumnProperty(name="partition_3", type="string")
            ],
            table_type="EXTERNAL_TABLE"
        )
    )

    # CloudWatch QuickSight SPICE Table
    cw_qs_spice_table = glue.CfnTable(
        stack, "CwQsSpiceTable",
        catalog_id=stack.account,
        database_name=admin_console_db.ref,
        table_input=glue.CfnTable.TableInputProperty(
            name=f"cw_qs_spice_{stack.account}",
            description="CloudWatch Metrics Stream data for QuickSight SPICE",
            parameters={
                "classification": "json",
                "partition_filtering.enabled": "true"
            },
            storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                columns=[
                    glue.CfnTable.ColumnProperty(name="metric_stream_name", type="string", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="account_id", type="string", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="region", type="string", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="namespace", type="string", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="metric_name", type="string", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="dimensions", type="struct<AccountId:string>", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="timestamp", type="bigint", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="value", type="struct<max:double,min:double,sum:double,count:double>", comment="from deserializer"),
                    glue.CfnTable.ColumnProperty(name="unit", type="string", comment="from deserializer")
                ],
                input_format="org.apache.hadoop.mapred.TextInputFormat",
                output_format="org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
                serde_info=glue.CfnTable.SerdeInfoProperty(
                    serialization_library="org.openx.data.jsonserde.JsonSerDe",
                    parameters={
                        "paths": "account_id,dimensions,metric_name,metric_stream_name,namespace,region,timestamp,unit,value"
                    }
                ),
                location=f"s3://cw-qs-spice-{stack.account}/"
            ),
            partition_keys=[
                glue.CfnTable.ColumnProperty(name="partition_0", type="string"),
                glue.CfnTable.ColumnProperty(name="partition_1", type="string"),
                glue.CfnTable.ColumnProperty(name="partition_2", type="string"),
                glue.CfnTable.ColumnProperty(name="partition_3", type="string")
            ],
            table_type="EXTERNAL_TABLE"
        )
    )

    return cw_qs_ds_table, cw_qs_dash_visual_table, cw_qs_spice_table