#!/bin/bash

name=$RANDOM
url='http://localhost:9093/api/v1/alerts'

echo "firing up alert $name" 

# change url o
curl -XPOST $url -d "[{ 
	\"status\": \"firing\",
	\"labels\": {
		\"alertname\": \"$name\",
		\"service\": \"deadman_check\",
		\"instance\": \"$name.example.net\",
                \"origin\": \"vna\"
	},
	\"annotations\": {
		\"summary\": \"lose connect to host $name\",
                \"severity\":\"critical\",
                \"value\":\"0\"
	},
	\"generatorURL\": \"http://kapacitor/<generating_expression>\"
}]"

echo ""
