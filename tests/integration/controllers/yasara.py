from serendip_api.controllers.yasara import make_yasara_scene


def test_yasara_scene():

    sequence = "TTCCPSIVARSNFNVCRLPGTPEAICATYTGCIIIPGATCPGDYAN"

    fake_data = [{"AliSeq": sequence[i], "prediction": "NI"} for i in range(len(sequence))]

    data = make_yasara_scene(fake_data)
