# CloudWatch QuickSight Dataset Table
resource "aws_glue_catalog_table" "cw_qs_ds" {
  name          = "cw_qs_ds"
  database_name = aws_glue_catalog_database.admin_console_db.name
  description   = "CloudWatch Metrics Stream data for QuickSight"

  table_type = "EXTERNAL_TABLE"

  parameters = {
    "classification"                = "json"
    "partition_filtering.enabled"   = "true"
  }

  storage_descriptor {
    location      = "s3://admin-suite-${data.aws_caller_identity.current.account_id}/cloudwatch/cw-qs-ds/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"
      parameters = {
        "paths" = "account_id,dimensions,metric_name,metric_stream_name,namespace,region,timestamp,unit,value"
      }
    }

    columns {
      name    = "metric_stream_name"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "account_id"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "region"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "namespace"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "metric_name"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "dimensions"
      type    = "struct<DatasetId:string>"
      comment = "from deserializer"
    }
    columns {
      name    = "timestamp"
      type    = "bigint"
      comment = "from deserializer"
    }
    columns {
      name    = "value"
      type    = "struct<max:double,min:double,sum:double,count:double>"
      comment = "from deserializer"
    }
    columns {
      name    = "unit"
      type    = "string"
      comment = "from deserializer"
    }
  }

  partition_keys {
    name = "partition_0"
    type = "string"
  }
  partition_keys {
    name = "partition_1"
    type = "string"
  }
  partition_keys {
    name = "partition_2"
    type = "string"
  }
  partition_keys {
    name = "partition_3"
    type = "string"
  }
}

# CloudWatch QuickSight Dashboard Visual Table
resource "aws_glue_catalog_table" "cw_qs_dash_visual" {
  name          = "cw_qs_dash_visual"
  database_name = aws_glue_catalog_database.admin_console_db.name
  description   = "CloudWatch Metrics Stream data for QuickSight Dashboard Visual"

  table_type = "EXTERNAL_TABLE"

  parameters = {
    "classification"                = "json"
    "partition_filtering.enabled"   = "true"
  }

  storage_descriptor {
    location      = "s3://admin-suite-${data.aws_caller_identity.current.account_id}/cloudwatch/cw-qs-dash-visual/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"
      parameters = {
        "paths" = "account_id,dimensions,metric_name,metric_stream_name,namespace,region,timestamp,unit,value"
      }
    }

    columns {
      name    = "metric_stream_name"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "account_id"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "region"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "namespace"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "metric_name"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "dimensions"
      type    = "struct<DashboardId:string,SheetId:string,VisualId:string>"
      comment = "from deserializer"
    }
    columns {
      name    = "timestamp"
      type    = "bigint"
      comment = "from deserializer"
    }
    columns {
      name    = "value"
      type    = "struct<max:double,min:double,sum:double,count:double>"
      comment = "from deserializer"
    }
    columns {
      name    = "unit"
      type    = "string"
      comment = "from deserializer"
    }
  }

  partition_keys {
    name = "partition_0"
    type = "string"
  }
  partition_keys {
    name = "partition_1"
    type = "string"
  }
  partition_keys {
    name = "partition_2"
    type = "string"
  }
  partition_keys {
    name = "partition_3"
    type = "string"
  }
}

# CloudWatch QuickSight SPICE Table
resource "aws_glue_catalog_table" "cw_qs_spice" {
  name          = "cw_qs_spice"
  database_name = aws_glue_catalog_database.admin_console_db.name
  description   = "CloudWatch Metrics Stream data for QuickSight SPICE"

  table_type = "EXTERNAL_TABLE"

  parameters = {
    "classification"                = "json"
    "partition_filtering.enabled"   = "true"
  }

  storage_descriptor {
    location      = "s3://admin-suite-${data.aws_caller_identity.current.account_id}/cloudwatch/cw-qs-spice/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"
      parameters = {
        "paths" = "account_id,dimensions,metric_name,metric_stream_name,namespace,region,timestamp,unit,value"
      }
    }

    columns {
      name    = "metric_stream_name"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "account_id"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "region"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "namespace"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "metric_name"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "dimensions"
      type    = "struct<AccountId:string>"
      comment = "from deserializer"
    }
    columns {
      name    = "timestamp"
      type    = "bigint"
      comment = "from deserializer"
    }
    columns {
      name    = "value"
      type    = "struct<max:double,min:double,sum:double,count:double>"
      comment = "from deserializer"
    }
    columns {
      name    = "unit"
      type    = "string"
      comment = "from deserializer"
    }
  }

  partition_keys {
    name = "partition_0"
    type = "string"
  }
  partition_keys {
    name = "partition_1"
    type = "string"
  }
  partition_keys {
    name = "partition_2"
    type = "string"
  }
  partition_keys {
    name = "partition_3"
    type = "string"
  }
}

# CloudWatch QuickSight QIndex Table
resource "aws_glue_catalog_table" "cw_qs_qindex" {
  name          = "cw_qs_qindex"
  database_name = aws_glue_catalog_database.admin_console_db.name
  description   = "CloudWatch Metrics Stream data for QuickSight Q Index"

  table_type = "EXTERNAL_TABLE"

  parameters = {
    "classification"                = "json"
    "partition_filtering.enabled"   = "true"
  }

  storage_descriptor {
    location      = "s3://admin-suite-${data.aws_caller_identity.current.account_id}/cloudwatch/cw-qs-qindex/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"
      parameters = {
        "paths" = "account_id,dimensions,metric_name,metric_stream_name,namespace,region,timestamp,unit,value"
      }
    }

    columns {
      name    = "metric_stream_name"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "account_id"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "region"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "namespace"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "metric_name"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "dimensions"
      type    = "struct<QuickInstanceId:string>"
      comment = "from deserializer"
    }
    columns {
      name    = "timestamp"
      type    = "bigint"
      comment = "from deserializer"
    }
    columns {
      name    = "value"
      type    = "struct<max:double,min:double,sum:double,count:double>"
      comment = "from deserializer"
    }
    columns {
      name    = "unit"
      type    = "string"
      comment = "from deserializer"
    }
  }

  partition_keys {
    name = "partition_0"
    type = "string"
  }
  partition_keys {
    name = "partition_1"
    type = "string"
  }
  partition_keys {
    name = "partition_2"
    type = "string"
  }
  partition_keys {
    name = "partition_3"
    type = "string"
  }
}

# CloudWatch QuickSight QAction Table
resource "aws_glue_catalog_table" "cw_qs_qaction" {
  name          = "cw_qs_qaction"
  database_name = aws_glue_catalog_database.admin_console_db.name
  description   = "CloudWatch Metrics Stream data for QuickSight Q Action"

  table_type = "EXTERNAL_TABLE"

  parameters = {
    "classification"                = "json"
    "partition_filtering.enabled"   = "true"
  }

  storage_descriptor {
    location      = "s3://admin-suite-${data.aws_caller_identity.current.account_id}/cloudwatch/cw-qs-qaction/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"
      parameters = {
        "paths" = "account_id,dimensions,metric_name,metric_stream_name,namespace,region,timestamp,unit,value"
      }
    }

    columns {
      name    = "metric_stream_name"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "account_id"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "region"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "namespace"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "metric_name"
      type    = "string"
      comment = "from deserializer"
    }
    columns {
      name    = "dimensions"
      type    = "struct<AccountId:string>"
      comment = "from deserializer"
    }
    columns {
      name    = "timestamp"
      type    = "bigint"
      comment = "from deserializer"
    }
    columns {
      name    = "value"
      type    = "struct<max:double,min:double,sum:double,count:double>"
      comment = "from deserializer"
    }
    columns {
      name    = "unit"
      type    = "string"
      comment = "from deserializer"
    }
  }

  partition_keys {
    name = "partition_0"
    type = "string"
  }
  partition_keys {
    name = "partition_1"
    type = "string"
  }
  partition_keys {
    name = "partition_2"
    type = "string"
  }
  partition_keys {
    name = "partition_3"
    type = "string"
  }
}