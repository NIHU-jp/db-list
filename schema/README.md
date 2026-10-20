# XML schemas

`catalogue.xsd` describes the independent `nihu:` wrapper, including optional
language-specific `nihu:listSummary` HTML fragments. Its namespace URI is
`urn:nihu-local:database-catalogue:1`; it does not claim an official NIHU schema.

The other XSD files are unchanged copies of the official JPCOAR 2.0 schema
(v2.0.0, 2022-12-01), retrieved 2026-10-19:
https://github.com/JPCOAR/schema/tree/master/2.0
The XML namespace schema is from https://www.w3.org/2001/03/xml.xsd .

The local resolver uses only these bundled schemas, so ordinary builds do not
fetch schemas from the network. HTML tag/attribute restrictions, the 500-character
summary limit, and duplicate summary-language checks are enforced by the runtime.
