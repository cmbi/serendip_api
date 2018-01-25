

def parse_serendip_results(data_string):

    lines = data_string.split('\n')
    header = lines[0]
    rows = lines[1:]

    field_ids = header.split()

    data = []
    for row in rows:
        entry = {}
        fields = row.split()
        for i in range(len(fields)):
            field_id = field_ids[i]
            entry[field_id] = fields[i]
        data.append(entry)

    return data
