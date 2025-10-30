output "group_membership" {
  description = "The s3 location of group_membership.csv for you to utilize in next Athena tables creation stack"
  value       = "s3://admin-console-new-${data.aws_caller_identity.current.account_id}/monitoring/quicksight/group_membership"
}

output "object_access" {
  description = "The s3 location of object_access.csv for you to utilize in next Athena tables creation stack"
  value       = "s3://admin-console-new-${data.aws_caller_identity.current.account_id}/monitoring/quicksight/object_access"
}

output "folder_assets" {
  description = "The s3 location of folder_assets.csv for you to utilize in next Athena tables creation stack"
  value       = "s3://admin-console-new-${data.aws_caller_identity.current.account_id}/monitoring/quicksight/folder_assets/folder_assets.csv"
}

output "folder_lk" {
  description = "The s3 location of folder_lk.csv for you to utilize in next Athena tables creation stack"
  value       = "s3://admin-console-new-${data.aws_caller_identity.current.account_id}/monitoring/quicksight/folder_lk/folder_lk.csv"
}

output "folder_path" {
  description = "The s3 location of folder_path.csv for you to utilize in next Athena tables creation stack"
  value       = "s3://admin-console-new-${data.aws_caller_identity.current.account_id}/monitoring/quicksight/folder_path/folder_path.csv"
}

output "datasets_properties" {
  description = "The s3 location of datasets_properties.csv for you to utilize in next Athena tables creation stack"
  value       = "s3://admin-console-new-${data.aws_caller_identity.current.account_id}/monitoring/quicksight/datasets_properties/datasets_properties.csv"
}

output "datasource_property" {
  description = "The s3 location of datasource_property.csv for you to utilize in next Athena tables creation stack"
  value       = "s3://admin-console-new-${data.aws_caller_identity.current.account_id}/monitoring/quicksight/datasource_property/datasource_property.csv"
}