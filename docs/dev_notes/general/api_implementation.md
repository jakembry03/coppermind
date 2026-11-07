# Website Integration

Static API key (bearer token)

    - Generate it with a cryptographically secure random generator (secrets module)
    - Store only a has of it in the database. SHA-256 is fine here because the key is long and random. bcrypt/argon2 are for passwords, which are short and guessable.
    - Compare hashes in constant time.
    - Give it a visible prefix and key ID (e.g. cpr_<id>_<secret>)
    - Set an expiry

On website:

generate key
hashlib.sha256(key.encode('utf-8')).hexdigest()

copper_api_pseudocode:
def post_request(request):
    if user_agent equal to "copper":
        if key_hash in database not equal to bearer auth_token:
            raise Error: invalid authentication token


    