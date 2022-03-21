#!/usr/bin/env python

import os
import json

zone_list=(
    "zone-name",
    "zone-name2"
)

gcp = "gcp"
ycp = "ycp"

def read_file(file_path, cloud):
    if cloud == "gcp":
        data_from_file = [line.strip() for line in open(file_path, 'r')]
    if cloud == "ycp":
        with open(file_path) as json_file:
            data_from_file = json.load(json_file)
    return data_from_file

def update_file(data, name):
    with open(name, "a") as open_file:
        open_file.write(data)

def remove_tmp_file(name):
    cmd = "rm " + name
    os.system(cmd)

def create_cmd_args_for_apply(records):
    args = ""
    for record in records:
        args += '--record \'{}\' '.format(record)

    return args

def export_records(zone, name, cloud):
    if cloud == "gcp":
        cmd = 'gcloud dns record-sets export {} --zone={} --zone-file-format'.format(name, zone)
    elif cloud == "ycp":
        cmd = 'yc dns zone list-records --name {} --format json > {}'.format(zone, name)
    returned_value = os.system(cmd)
    if returned_value > 0:
        os._exit(returned_value)

def import_records(zone, records, action):
    if action == "add":
        cmd = 'yc dns zone add-records --name {} {}'.format(zone, records)
    if action == "delete":
        cmd = 'yc dns zone delete-records --name {} {}'.format(zone, records)
    print(cmd)
    returned_value = os.system(cmd)
    if returned_value > 0:
        os._exit(returned_value)

if __name__ == '__main__':
    for zone in zone_list:
        zone_records_old=[]
        zone_records_new=[]
        zone_records_to_apply= []
        zone_records_to_delete= []
        update_str = ""
        delete_str = ""
        file_old = '{}.zonefile_ycp'.format(zone)
        file_new = '{}.zonefile_gcp'.format(zone)

        export_records(zone, file_old, ycp)
        export_records(zone, file_new, gcp)

        raw_records_old = read_file(file_old, ycp)
        raw_records_new = read_file(file_new, gcp)

        for record in raw_records_old:
            if record['type'] == "NS":
                pass
            elif record['type'] == "SOA":
                pass
            else:
                for data_record in record['data']:
                    formated_record_old = "{} {} {} {}".format(record['name'],record['ttl'],record['type'],data_record)
                    zone_records_old.append(formated_record_old)

        for record in raw_records_new:
            if "SOA" in record:
                pass
            elif "NS" in record:
                pass
            else:
                tmp_record = record.split()
                del tmp_record[2]
                updated_record = " ".join(tmp_record)
                zone_records_new.append(updated_record)

        zone_records_new.sort()
        zone_records_old.sort()

        for zone_record in zone_records_new:
            if zone_record in zone_records_old:
                pass
            else:
                zone_records_to_apply.append(zone_record)

        for zone_record in zone_records_old:
            if zone_record in zone_records_new:
                pass
            else:
                zone_records_to_delete.append(zone_record)

        if len(zone_records_to_apply) > 0:
            for record in zone_records_to_apply:
                update_str += "".join(record) + "\n"
            import_records(zone, create_cmd_args_for_apply(zone_records_to_apply), "add")

        if len(zone_records_to_delete) > 0:
            for record in zone_records_to_delete:
                delete_str += "".join(record) + "\n"
            import_records(zone, create_cmd_args_for_apply(zone_records_to_delete), "delete")

        print("\n\nUpdated records:")
        print("\n\tZone {} add:".format(zone))
        if len(update_str) > 0:
            print(update_str)
        else:
            print("\t\tNone")
        print("\n\tZone {} delete:".format(zone))
        if len(delete_str) > 0:
            print(delete_str)
        else:
            print("\t\tNone")

        remove_tmp_file(file_new)
        remove_tmp_file(file_old)
