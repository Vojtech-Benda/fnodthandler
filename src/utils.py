


def split_pacs_fields(pacs_fields: str):
    tokens = pacs_fields.split('-')
    return tokens[0], tokens[1], tokens[2]
    
    