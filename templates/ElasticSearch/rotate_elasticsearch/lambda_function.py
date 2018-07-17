# https://docs.aws.amazon.com/elasticsearch-service/latest/developerguide/curator.html

import boto3
import threading
import curator

from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection

service = 'es'
credentials = boto3.Session().get_credentials()

# event example:
# { "region": "eu-west-1", "host": "vpc-ams-xhokskxuqndwgyrboxu3raioki.eu-west-1.es.amazonaws.com", "port": 443, "unit": "weeks", "count": 4 }
def lambda_handler(event, context):

    print(event)

    # to catch lambda timeout
    timer = threading.Timer((context.get_remaining_time_in_millis() / 1000.00) - 0.5, timeout, args=[event, context])
    timer.start()

    try:

        awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, event['region'], service, session_token=credentials.token)
        
        # Build the Elasticsearch client.
        es = Elasticsearch(
            hosts = [{'host': event['host'], 'port': event['port']}],
            http_auth = awsauth,
            use_ssl = True,
            verify_certs = True,
            connection_class = RequestsHttpConnection
        )

        index_list = curator.IndexList(es)
        
        # Filters by age, anything created more than x weeks ago.
        index_list.filter_by_age(source='creation_date', direction='older', unit=event['unit'], unit_count=event['count'])
        
        # Delete all indices in the filtered list.
        result = curator.DeleteIndices(index_list).do_action()

        return result

    except Exception as e:
        print('Function failed due to exception:')
        print(e)

        raise Exception('unexpected error (check the lambda logs)')

    finally:
        timer.cancel()

def timeout(event, context):

    print('Execution is about to time out')
    raise Exception('timeout exception (check the lambda logs)')