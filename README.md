# UFO Files Data Archive

[![Live archive count](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fufo-files%2Fdata-archive-1%2Farchive-count%2Farchive-count.json&query=%24.count&label=archived%20files&color=111111)](https://raw.githubusercontent.com/ufo-files/data-archive-1/archive-count/archive-count.json)
[![Archive shards](https://img.shields.io/badge/archive%20shards-3-111111)](#archive-directory)

This is the base shard of the [UFO Files](https://ufo-files.app) public source
archive. It preserves original source material while retaining the
source-relative paths used across the archive.

The archive is split across multiple GitHub repositories to keep it browsable
as it grows. A source folder may appear in more than one shard; those folders
contain different portions of the same collection.

## Archive Directory

| Repository | Purpose | Folders |
| --- | --- | --- |
| [`data-archive`](https://github.com/ufo-files/data-archive) | Base archive shard and broad source index | [`AARO-UAP-Records`](https://github.com/ufo-files/data-archive/tree/main/AARO-UAP-Records)<br>[`American-Alchemy`](https://github.com/ufo-files/data-archive/tree/main/American-Alchemy)<br>[`Black-Vault-UFO`](https://github.com/ufo-files/data-archive/tree/main/Black-Vault-UFO)<br>[`DOE-NNSA-UAP-UFO`](https://github.com/ufo-files/data-archive/tree/main/DOE-NNSA-UAP-UFO)<br>[`DPIArchive`](https://github.com/ufo-files/data-archive/tree/main/DPIArchive)<br>[`FBI-Vault-UFO`](https://github.com/ufo-files/data-archive/tree/main/FBI-Vault-UFO)<br>[`Legacy-Documents`](https://github.com/ufo-files/data-archive/tree/main/Legacy-Documents)<br>[`NSA-UFO-FOIA`](https://github.com/ufo-files/data-archive/tree/main/NSA-UFO-FOIA)<br>[`National-Archives-UAP-Bulk`](https://github.com/ufo-files/data-archive/tree/main/National-Archives-UAP-Bulk)<br>[`Steven-Greer-Document-Library`](https://github.com/ufo-files/data-archive/tree/main/Steven-Greer-Document-Library)<br>[`War-Gov-PURSUE`](https://github.com/ufo-files/data-archive/tree/main/War-Gov-PURSUE)<br>[`wikileaks`](https://github.com/ufo-files/data-archive/tree/main/wikileaks) |
| [`data-archive-1`](https://github.com/ufo-files/data-archive-1) | Archive shard 1 and canonical live-count publisher | [`National-Archives-UAP-Bulk`](https://github.com/ufo-files/data-archive-1/tree/main/National-Archives-UAP-Bulk) |
| [`data-archive-2`](https://github.com/ufo-files/data-archive-2) | Archive shard 2 | [`National-Archives-UAP-Bulk`](https://github.com/ufo-files/data-archive-2/tree/main/National-Archives-UAP-Bulk) |

## Live Count

The [`archive-count` branch](https://github.com/ufo-files/data-archive-1/tree/archive-count)
publishes the canonical machine-readable
[`archive-count.json`](https://raw.githubusercontent.com/ufo-files/data-archive-1/archive-count/archive-count.json).

It inventories the union of every numbered archive shard and deduplicates
matching relative paths. ZIP packages, temporary files, processing state, and
derived OCR or transcript output are excluded from the public source-file count.

## What Is Preserved

- Original PDFs, images, videos, audio, and other downloaded source files
- Source-specific folder names and relative paths
- Manifests, checksums, and collection metadata where supplied by the archiver
- Git history showing when files entered the public archive

## Finding Derived Data

Searchable OCR, transcripts, thumbnails, and normalized corpus records live in
[`ufo-files/data`](https://github.com/ufo-files/data). Explore relationships
derived from that corpus in the
[`relationship-graph`](https://github.com/ufo-files/relationship-graph).

## Provenance

An archived file records what a source published; its presence does not verify
the claims it contains or imply endorsement by UFO Files. Source material may
include disputed, historical, testimonial, journalistic, or government records.

Consult each file's collection metadata and original publisher when evaluating
provenance.
