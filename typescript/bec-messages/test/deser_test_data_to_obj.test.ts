import { describe, expect, it } from "vitest";
import { encode, decode } from "@msgpack/msgpack";
import { default as Ajv } from "ajv";
import * as fs from 'fs';
import * as MessageTypes from "../src"

const ajv = new Ajv();

describe("decoding test message to struct succeeds", () => {
  it.each(Object.keys(MessageTypes))("for message %s", (message_type) => {
    let binary = fs.readFileSync(`../../test_data/${message_type}`, null);
    console.log(binary);
    let deser = decode(binary);
    console.log(deser);
    let schema = JSON.parse(fs.readFileSync(`../../json_schema/${message_type}.json`, 'utf8'));
    console.log(schema);
    ajv.validate(schema, deser);
  });
});
