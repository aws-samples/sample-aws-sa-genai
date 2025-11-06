# Quick Admin Suite – Glue Job Mapping

If you are using the solution described in the blog post  
[**Measure the adoption of your Amazon QuickSight dashboards and view your BI portfolio in a single pane of glass**](https://aws.amazon.com/blogs/business-intelligence/measure-the-adoption-of-your-amazon-quicksight-dashboards-and-view-your-bi-portfolio-in-a-single-pane-of-glass/),  
this document provides the mapping between the Glue jobs in that solution and the corresponding jobs in the older solution.

## Glue Job Mapping

| New Solution Glue Job | Old Solution Glue Job | Notes |
|------------------------|-----------------------|-------|
| `admin_suite_data_dictionary`     | `adminconsoledatasetdashboardinfo`    | Data transformation logic updated |
| `admin_suite_user_info_access_manage`     | `adminconsoleuserdataaccessinfo`    |  |
| `admin_suite_folder_info`          | `adminconsolefolderinfo`| new glue job  |
| `admin_suite_q_topic_info`     | `adminconsoleqtopicinfo`    | new glue job |
| `admin_suite_q_topic_access`          | `adminconsoleqobjectaccessinfo`| new glue job  |


## How to Use

1. Identify the Glue job you are running in the new solution.  
2. Use the table above to find the equivalent job from the older solution.  
3. Refer to the **Notes** column for details on changes in logic, structure, or dependencies.



## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

