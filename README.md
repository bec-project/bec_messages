# BEC Messages RFC 0.0.1

- Status: open
- Stakeholders: BEC development team
- Last edited: 13/01/2026

## Motivation

BEC comprises multiple services communicating through a central Redis database.
To facilitate the interoperability of various services relying on messages
within the BEC ecosystem we require a clear specification for such messages.
Different services MAY be written in different programming languages (Python,
JavaScript/TypeScript, Rust, Swift, etc.) but MUST produce messages conformant
to this specification.

## Proposed implementation

### Message specification

Individual message types SHALL continue to be written in the _Pydantic_ model
format. Messages SHALL be defined in this repository. The JSON schema which is
generated from these models constitute the canonical definition of each message
type. Messages produced by libraries in other languages MUST conform to the
JSON schema. Where possible, data structures to represent messages in other
languages SHOULD be generated programatically from the JSON schema.

### Additional validation logic

_Pydantic_ allows for the implementation of custom validation logic. In Python
clients, these are used directly. Libraries in other languages SHOULD implement
equivalent validation logic. If they do not, those libraries SHOULD NOT expose
message types which require them.

### Encoding

Messages MUST be encoded using the [MessagePack](https://msgpack.org/) format.
Not all datatypes in use in BEC are represented in the MessagePack
specification. Any BEC Messages library may implement additional encoder
definitions. For each additional datatype, one language MUST define a canonical
encoding and decoding mechanism. Libraries in other languages SHOULD implement
equivalent logic. If they do not, they SHOULD NOT expose message types which
require them.
