from opensearchpy import OpenSearch
import datetime

client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    http_compress=True,  # optional
    http_auth=("admin", "Strong_Password123!"),
    use_ssl=True,
    verify_certs=False,  # <- Important: self-signed SSL cert
    ssl_show_warn=False,  # <- Optional: don't spam SSL warnings
)

info = client.info()
print(info)


# Create an index called "honeypot-logs" with a basic mapping
index_name = "honeypot-logs"

# # Define a simple mapping for the index (optional but recommended)
# mapping = {
#     "settings": {
#         "number_of_shards": 1,
#         "number_of_replicas": 0   # 0 replicas since we have one node (for demo)
#     },
#     "mappings": {
#         "properties": {
#             "timestamp":   {"type": "date"},        # log time
#             "honeypot":    {"type": "keyword"},     # type of honeypot
#             "attacker_ip": {"type": "ip"},          # IP address type
#             "attacker_port": {"type": "integer"},   # port number
#             "user_agent":  {"type": "text"},        # user agent string (if any)
#             "username":    {"type": "keyword"},     # attempted username
#             "password":    {"type": "keyword"},     # attempted password
#             "commands":    {"type": "text"},        # commands executed
#             "country":     {"type": "keyword"}      # country of origin
#         }
#     }
# }

# response = client.indices.create(index=index_name, body=mapping, ignore=400)
# # ignore=400 will ignore error if index already exists
# print(response)

# doc = {
#     "timestamp": datetime.datetime.now().isoformat(),
#     "honeypot": "ssh", 
#     "attacker_ip": "192.0.2.123",
#     "attacker_port": 22,
#     "user_agent": "N/A",  # not applicable for SSH, but just for example
#     "username": "root",
#     "password": "123456",
#     "commands": "echo 'hacked'",
#     "country": "US"
# }

# # Index the document into "honeypot-logs" index
# resp = client.index(index=index_name, body=doc)
# print(resp)

# # Index another sample document
# doc2 = {
#     "timestamp": (datetime.datetime.now() - datetime.timedelta(minutes=5)).isoformat(),
#     "honeypot": "ssh",
#     "attacker_ip": "203.0.113.45",
#     "attacker_port": 22,
#     "user_agent": "N/A",
#     "username": "admin",
#     "password": "password",
#     "commands": "uname -a",
#     "country": "CN"
# }
# client.index(index=index_name, body=doc2)

# # Index one more sample document
# doc3 = {
#     "timestamp": (datetime.datetime.now() - datetime.timedelta(hours=1)).isoformat(),
#     "honeypot": "web",
#     "attacker_ip": "198.51.100.10",
#     "attacker_port": 80,
#     "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",  # a fake user agent
#     "username": "admin",
#     "password": "admin",
#     "commands": "GET /etc/passwd",
#     "country": "RU"
# }
# client.index(index=index_name, body=doc3)


# Search for a document with attacker_ip "203.0.113.45" to get its ID
# search_resp = client.search(
#     index=index_name,
#     body={
#         "query": {
#             "term": {
#                 "attacker_ip": "203.0.113.45"
#             }
#         }
#     }
# )

# # Assuming we got an ID from the search
# doc_id = search_resp["hits"]["hits"][0]["_id"]

# # Get the document by ID
# get_resp = client.get(index=index_name, id=doc_id)
# print(get_resp["_source"])


# # Update a document (partial update) by ID
# update_fields = {
#     "doc": {  # fields to update
#         "password": "123456789"  # perhaps we discovered the attacker tried a longer password later
#     }
# }
# update_resp = client.update(index=index_name, id=doc_id, body=update_fields)
# print(update_resp)

# get_resp = client.get(index=index_name, id=doc_id)
# print(get_resp["_source"])


# Searching for all SSH honeypot attacks from China (country = "CN")
query = {
    "query": {
        "bool": {
            "must": [
                {"term": {"honeypot": "ssh"}}
            ]
        }
    }
}
search_results = client.search(index=index_name, body=query)
for hit in search_results["hits"]["hits"]:
    print(hit["_source"])
