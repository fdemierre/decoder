import base64

def decode_adeunis(base64_payload):
    bytes_ = list(base64.b64decode(base64_payload))
    bytes_len = len(bytes_)
    bytes_pos = 1
    payload = {}

    # 📦 Métadonnées sur le décodeur et l'appareil
    payload["decoder_metadata"] = {
        "decoder_version": "1.0.0",
        "description": "FieldTest",
        "company": "Adeunis",
        "model": "ARF8123AA",
        "field_structure": {
            0: {"name": "temperature", "type": "int", "unit": "°C"},
            1: {"name": "trigger", "type": "string", "value": "accelerometer"},
            2: {"name": "trigger", "type": "string", "value": "pushbutton"},
            3: {"name": "gps", "fields": ["latitude", "longitude", "sats", "hdop", "gps_quality"]},
            4: {"name": "ul_counter", "type": "int"},
            5: {"name": "dl_counter", "type": "int"},
            6: {"name": "battery_level", "type": "int", "unit": "mV"},
            7: {"name": "downlink", "fields": ["rssi_dl", "snr_dl"], "unit": "dB"}
        }
    }

    def parse_coordinate(raw_value, coordinate):
        raw_itude = raw_value
        temp = ""

        itude_string = str((raw_itude >> 28) & 0xF)
        raw_itude <<= 4
        itude_string += str((raw_itude >> 28) & 0xF)
        raw_itude <<= 4
        coordinate["degrees"] += itude_string
        itude_string += "°"

        temp = str((raw_itude >> 28) & 0xF)
        raw_itude <<= 4
        temp += str((raw_itude >> 28) & 0xF)
        raw_itude <<= 4
        itude_string += temp
        itude_string += "."
        coordinate["minutes"] += temp

        temp = str((raw_itude >> 28) & 0xF)
        raw_itude <<= 4
        temp += str((raw_itude >> 28) & 0xF)
        raw_itude <<= 4
        itude_string += temp
        coordinate["minutes"] += "." + temp

        return itude_string

    def parse_latitude(raw_latitude, coordinate):
        lat = parse_coordinate(raw_latitude, coordinate)
        last_digit = (raw_latitude & 0xF0) >> 4
        lat += str(last_digit)
        coordinate["minutes"] += str(last_digit)
        return lat

    def parse_longitude(raw_longitude, coordinate):
        coordinate["degrees"] = str((raw_longitude >> 28) & 0xF)
        return coordinate["degrees"] + parse_coordinate(raw_longitude << 4, coordinate)

    def add_field(field_no):
        nonlocal bytes_pos
        if field_no == 0:
            temp = bytes_[bytes_pos] & 0x7F
            if (bytes_[bytes_pos] & 0x80) > 0:
                temp -= 128
            payload["temperature"] = temp
            bytes_pos += 1

        elif field_no == 1:
            payload["trigger"] = "accelerometer"

        elif field_no == 2:
            payload["trigger"] = "pushbutton"

        elif field_no == 3:
            coordinate = {"degrees": "", "minutes": ""}

            raw_lat = (bytes_[bytes_pos] << 24) | (bytes_[bytes_pos+1] << 16) | (bytes_[bytes_pos+2] << 8) | bytes_[bytes_pos+3]
            bytes_pos += 4
            payload["lati_hemisphere"] = "South" if (raw_lat & 1) == 1 else "North"
            payload["latitude_dmm"] = payload["lati_hemisphere"][0] + " " + parse_latitude(raw_lat, coordinate)
            payload["latitude"] = (float(coordinate["degrees"]) + float(coordinate["minutes"]) / 60.0) * (-1 if payload["lati_hemisphere"] == "South" else 1)

            coordinate = {"degrees": "", "minutes": ""}
            raw_lon = (bytes_[bytes_pos] << 24) | (bytes_[bytes_pos+1] << 16) | (bytes_[bytes_pos+2] << 8) | bytes_[bytes_pos+3]
            bytes_pos += 4
            payload["long_hemisphere"] = "West" if (raw_lon & 1) == 1 else "East"
            payload["longitude_dmm"] = payload["long_hemisphere"][0] + " " + parse_longitude(raw_lon, coordinate)
            payload["longitude"] = (float(coordinate["degrees"]) + float(coordinate["minutes"]) / 60.0) * (-1 if payload["long_hemisphere"] == "West" else 1)

            gps_byte = bytes_[bytes_pos]
            bytes_pos += 1
            gps_quality_map = {1: "Good", 2: "Average", 3: "Poor"}
            quality = (gps_byte >> 4) & 0xF
            payload["gps_quality"] = gps_quality_map.get(quality, quality)
            payload["hdop"] = quality
            payload["sats"] = gps_byte & 0xF

        elif field_no == 4:
            payload["ul_counter"] = bytes_[bytes_pos]
            bytes_pos += 1

        elif field_no == 5:
            payload["dl_counter"] = bytes_[bytes_pos]
            bytes_pos += 1

        elif field_no == 6:
            payload["battery_level"] = (bytes_[bytes_pos] << 8) | bytes_[bytes_pos+1]
            bytes_pos += 2

        elif field_no == 7:
            payload["rssi_dl"] = -bytes_[bytes_pos]
            bytes_pos += 1
            snr = bytes_[bytes_pos] & 0x7F
            if bytes_[bytes_pos] & 0x80:
                snr -= 128
            payload["snr_dl"] = snr
            bytes_pos += 1

    # Décodage du champ status
    status = bytes_[0]
    i = 0
    while (status & 0x80) > 0:
        add_field(i)
        status = (status << 1) & 0xFF
        i += 1

    payload["raw_payload"] = ''.join(f"{b:02X}" for b in bytes_)

    # 📋 Log de debug console (optionnel)
    print("\n=== Decoder Metadata ===")
    for k, v in payload["decoder_metadata"].items():
        print(f"{k}: {v}")

    return payload


# 🔍 Exemple d’utilisation
if __name__ == "__main__":
    payload = "nhhGRokAAGOVYBbSCBBq"  # Exemple base64
    result = decode_adeunis(payload)
    from pprint import pprint
    pprint(result)
