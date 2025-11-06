import boto3
import time
import sys

def trigger_crawlers():
    """Trigger all QuickSight admin suite crawlers sequentially"""
    
    glue_client = boto3.client('glue')
    
    # List of crawlers to trigger in order
    crawlers = [
        'crawler-cw-qs-ds',
        'crawler-cw-qs-spice', 
        'crawler-cw-qs-qindex',
        'crawler-cw-qs-qaction',
        'crawler-cw-qs-dash-visual'
    ]
    
    print(f"Starting crawler trigger job for {len(crawlers)} crawlers")
    
    for crawler_name in crawlers:
        try:
            print(f"Triggering crawler: {crawler_name}")
            
            # Start the crawler
            response = glue_client.start_crawler(Name=crawler_name)
            print(f"Successfully triggered {crawler_name}")
            
            # Wait a bit between crawler starts to avoid resource conflicts
            time.sleep(30)
            
        except glue_client.exceptions.CrawlerRunningException:
            print(f"Crawler {crawler_name} is already running, skipping")
            
        except Exception as e:
            print(f"Error triggering crawler {crawler_name}: {str(e)}")
            # Continue with other crawlers even if one fails
            continue
    
    print("Crawler trigger job completed")

if __name__ == "__main__":
    trigger_crawlers()