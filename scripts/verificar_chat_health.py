"""Verifica el stack T15 sin imprimir la API key."""

import json
import urllib.error
import urllib.request

import boto3


def main():
    session = boto3.Session(profile_name="hackaton", region_name="us-east-1")
    stack = session.client("cloudformation").describe_stacks(StackName="ChileAtiendeChat")
    outputs = {x["OutputKey"]: x["OutputValue"] for x in stack["Stacks"][0]["Outputs"]}
    endpoint = outputs["Url"] + "/health"
    key = session.client("secretsmanager").get_secret_value(SecretId=outputs["ApiKeySecret"])[
        "SecretString"
    ]
    for supplied, expected in ((None, (401, 403)), ("invalid", (401, 403)), (key, (200,))):
        request = urllib.request.Request(
            endpoint, headers={"x-api-key": supplied} if supplied else {}
        )
        try:
            with urllib.request.urlopen(request, timeout=35) as result:
                status, body = result.status, json.load(result)
        except urllib.error.HTTPError as error:
            status, body = error.code, json.load(error)
        assert status in expected, (status, body)
        print(f"{'Con key' if supplied == key else 'Sin key válida'}: HTTP {status}")
        if status == 200:
            assert body["ok"] and body["data"]["bedrock"]
            print("Lambda → Bedrock: OK")


if __name__ == "__main__":
    main()
