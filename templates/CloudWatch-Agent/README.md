# HOWTOs


## NOTES

### Multiple LogGroups

If you use multiple LogGroups with a unique Lambda, remember to change the index name to include the log group (ES 6.2 issue):


``` js
  var indexName = [
            'cwl-' +  payload.logGroup.replace(/\//g,'-') + '-' + timestamp.getUTCFullYear(),              // year
            ('0' + (timestamp.getUTCMonth() + 1)).slice(-2),  // month
            ('0' + timestamp.getUTCDate()).slice(-2)          // day
        ].join('.');
```

### Filter Examples

IIS Filter: ```[date, time, sitename, computername, sip, method, uri, query, port, username, cip, version, agent, cookie, referer, host, status, substatus, win32status, scbytes, csbytes, timetaken]```

Application Filter: ```[date, time, utc, level, scope, message]```

## ElasticSearch Ops

C:\curl\bin\curl -XGET https://vpc-ams-xhokskxuqndwgyrboxu3raioki.eu-west-1.es.amazonaws.com/_cat/indices?v
C:\curl\bin\curl -XDELETE https://vpc-ams-xhokskxuqndwgyrboxu3raioki.eu-west-1.es.amazonaws.com/cwl-2018.05.10

