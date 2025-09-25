import aws_cdk as core
import aws_cdk.assertions as assertions

from data_collection.data_collection_stack import DataCollectionStack

# example tests. To run these tests, uncomment this file along with the example
# resource in data_collection/data_collection_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = DataCollectionStack(app, "data-collection")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
