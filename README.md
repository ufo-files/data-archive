 97 +                        "last_downloaded": "-",
   98 +                    },
   99 +                )
  100 +            finally:
  101 +                update_epaper_status.ARCHIVE_DIR_BY_SITE = original
  102 +
  103 +        self.assertEqual(reconciled["status"], "up-to-date")
  104 +        self.assertEqual(reconciled["last_checked"], "2026-07-20T07:53:07Z")
  105 +        self.assertEqual(reconciled["last_downloaded"], "2026-07-19T14:05:01Z")
  106 +
  107      def test_explicit_download_timestamp_precedes_file_mtime(self):

└ /private/tmp/ufo-files-agents-current/scripts/update_epaper_status.py (+37 -0)
  1147              continue
  1148 +        row = reconcile_cached_archiver_status(site, row)
  1149          statuses.append(
       ⋮
  1163
  1164 +def reconcile_cached_archiver_status(site: str, cached: dict[str, object]) -> dict[str, ob
        ject]:
  1165 +    archive_dir = ARCHIVE_DIR_BY_SITE.get(site)
  1166 +    if archive_dir is None:
  1167 +        return cached
  1168 +    manifest_path = archive_manifest_path(archive_dir)
  1169 +    try:
  1170 +        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
  1171 +    except (OSError, json.JSONDecodeError):
  1172 +        return cached
  1173 +    if not isinstance(manifest, dict):
  1174 +        return cached
  1175 +
  1176 +    manifest_checked = str(manifest.get("last_checked_at") or "")
  1177 +    manifest_time = parse_manifest_datetime(manifest_checked)
  1178 +    cached_time = parse_manifest_datetime(cached.get("last_checked"))
  1179 +    if manifest_time is None or (cached_time is not None and manifest_time < cached_time):
  1180 +        return cached
  1181 +
  1182 +    run_status = str(manifest.get("run_status") or "").casefold()
  1183 +    if run_status == "complete":
  1184 +        status = "up-to-date"
  1185 +    elif run_status in {"error", "incomplete"}:
  1186 +        status = "error"
  1187 +    elif run_status == "running":
  1188 +        status = "checking"
  1189 +    else:
  1190 +        return cached
  1191 +
  1192 +    reconciled = dict(cached)
  1193 +    reconciled["status"] = status
  1194 +    reconciled["last_checked"] = manifest_checked
  1195 +    reconciled["archived"] = format_count(archived_count_from_manifest(manifest, archive_d
        ir))
  1196 +    reconciled["last_downloaded"] = last_downloaded_from_manifest(manifest, archive_dir)
  1197 +    return reconciled
  1198 +
  1199 +
  1200  def read_status_cache_from_log() -> dict[str, dict[str, object]]:

• Ran /private/tmp/ufo-agents-test-venv/bin/python -m unittest
│ scripts.tests.test_update_epaper_status -v && python3 -m py_compile scripts/
│ update_epaper_status.py && git diff --check
└ test_active_source_percentage_has_staging_arrow
  (scripts.tests.test_update_epaper_status.PublisherEpaperStatusTests.test_active_source_percentag
  … +30 lines (ctrl + t to view transcript)

  OK

• Ran git add scripts/update_epaper_status.py scripts/tests/test_update_epaper_status.py && git
│ commit -m "Reconcile archiver status with newer manifests" && git push origin master
└ To https://github.com/ufo-files/agents.git
     a932d23..6361b5a  master -> master

────────────────────────────────────────────────────────────────────────────────────────────────────

• The fix is pushed. I’m checking whether this session can deploy it to the Pi directly; if the
encrypted SSH key is not loaded, I’ll give you one command that pulls the fix and immediately
verifies AARO against its successful manifest.

• Ran ssh -o BatchMode=yes -o ConnectTimeout=8 -i /Users/glennsorrentino/.ssh/ufo_agent_pi_ed25519
│ ufo-agent@192.168.0.131 'cd /home/ufo-agent/agents && git pull --ff-only origin master && ./
│ scripts/update_epaper_status.py --status-table'
└ ufo-agent@192.168.0.131: Permission denied (publickey).

────────────────────────────────────────────────────────────────────────────────────────────────────

• The Pi key is encrypted and not loaded in this session, so direct deployment was rejected. I also
caught that the physical e-paper render uses a separate live-state path from the terminal table;
I’m applying the same “newer completed manifest wins over stale error” rule there before I hand
back the deploy command.

• Edited 2 files (+31 -2)
└ /private/tmp/ufo-files-agents-current/scripts/tests/test_update_epaper_status.py (+17 -0)
  106
  107 +    def test_newer_manifest_status_overrides_stale_error_state(self):
  108 +        original = update_epaper_status.read_archiver_state
  109 +        try:
  110 +            update_epaper_status.read_archiver_state = lambda _archiver_id: {
  111 +                "status": "error",
  112 +                "updated_at": "2026-07-19T07:02:06Z",
  113 +            }
  114 +            status = update_epaper_status.display_status_from_state(
  115 +                "aaro-uap-records",
  116 +                "No new downloads",
  117 +                fallback_updated_at="2026-07-20 07:53:07 UTC",
  118 +            )
  119 +        finally:
  120 +            update_epaper_status.read_archiver_state = original
  121 +
  122 +        self.assertEqual(status, "No new downloads")
  123 +
  124      def test_explicit_download_timestamp_precedes_file_mtime(self):

└ /private/tmp/ufo-files-agents-current/scripts/update_epaper_status.py (+14 -2)
  1684          last_checked=display_last_checked(archiver_id, last_checked),
  1685 -        status=display_status_from_state(archiver_id, "running" if running else download_s
        tatus(manifest_path, ("downloaded",))),
  1685 +        status=display_status_from_state(
  1686 +            archiver_id,
  1687 +            "running" if running else download_status(manifest_path, ("downloaded",)),
  1688 +            fallback_updated_at=last_checked,
  1689 +        ),
  1690          archived=archived,
       ⋮
  2456
  2453 -def display_status_from_state(archiver_id: str, fallback: str) -> str:
  2457 +def display_status_from_state(
  2458 +    archiver_id: str,
  2459 +    fallback: str,
  2460 +    fallback_updated_at: str = "",
  2461 +) -> str:
  2462      state = read_archiver_state(archiver_id)
       ⋮
  2474          return "checking" if status == "indexing" else status
  2475 +    state_time = parse_manifest_datetime(state.get("updated_at"))
  2476 +    fallback_time = parse_manifest_datetime(fallback_updated_at)
  2477 +    if fallback_time is not None and state_time is not None and fallback_time >= state_tim
        e:
  2478 +        return fallback
  2479      return status

• Ran /private/tmp/ufo-agents-test-venv/bin/python -m unittest
│ scripts.tests.test_update_epaper_status -v && python3 -m py_compile scripts/
│ update_epaper_status.py && git diff --check && git add scripts/update_epaper_status.py
│ … +2 lines
└ test_active_source_percentage_has_staging_arrow
  (scripts.tests.test_update_epaper_status.PublisherEpaperStatusTests.test_active_source_percentag
  … +35 lines (ctrl + t to view transcript)
  fatal: unable to access 'https://github.com/ufo-files/agents.git/': Could not resolve host:
  github.com

• Ran git push origin master
└ To https://github.com/ufo-files/agents.git
     6361b5a..0c882e1  master -> master

────────────────────────────────────────────────────────────────────────────────────────────────────

• AARO itself succeeded: 11 records found, 11 present, 0 failures. The error was stale display
state.

Fix pushed in 0c882e1; all 20 e-paper tests pass. Pull and refresh:

ssh -t -i ~/.ssh/ufo_agent_pi_ed25519 ufo-agent@192.168.0.131 'cd /home/ufo-agent/agents && git
pull --ff-only origin master && ./scripts/update_epaper_status.py'

My direct deployment was blocked because the SSH key requires your passphrase.

─ Worked for 3m 38s ────────────────────────────────────────────────────────────────────────────────


› wheres the mf tab;e


• I omitted --status-table from the last command. Use:

ssh -t -i ~/.ssh/ufo_agent_pi_ed25519 ufo-agent@192.168.0.131 'cd /home/ufo-agent/agents && git
pull --ff-only origin master && ./scripts/update_epaper_status.py --status-table'

For a continuously refreshing table:

ssh -t -i ~/.ssh/ufo_agent_pi_ed25519 ufo-agent@192.168.0.131 'cd /home/ufo-agent/agents && while
true; do clear; ./scripts/update_epaper_status.py --status-table; sleep 30; done'


› i see "2026-07-20T08:12:05Z HEARTBEAT phase=preseed-transport
remote: warning: Repository is approaching its size quota.
To https://github.com/ufo-files/data-archive-1.git
   a5ecf47e..d3274f07  d3274f07c9ecc60a72ebcce8f3f4e0cb84c71f6a -> archive-publisher-staging
2026-07-20T08:12:17Z PUSH attempt=1/8 sha=e27e4b9961cb69764ea8888801e8698ed02633d1
2026-07-20T08:12:20Z HEARTBEAT phase=push-attempt-1" - will a new repo data-archive-2 be created
automatically?


• I’m checking the publisher’s quota rollover logic directly. The warning alone does not prove it
will create data-archive-2; I’ll confirm the exact trigger and whether repository creation is
automatic.

• Explored
└ Search data-archive-2|archive-[0-9]|size quota|quota|create.*repo|gh repo create|rollover|next
repo|
         repository.*full|data-archive- in scripts
  List rg --files
  Search quota|rollover|next.*repo|repo.*create|gh.*repo|data-archive-[0-9]|Repository is
  approaching|
         staging|preseed in data-archive
  Read README.md, publish_under_100_shards.py

• Ran gh api repos/ufo-files/data-archive-1 --jq '{name,size_kb,default_branch}'
└ {"default_branch":"main","name":"data-archive-1","size_kb":null}

• Ran gh api repos/ufo-files/data-archive-1 --jq '{name: .name, size_kb: .size, size_gib: (.size /
│ 1048576), default_branch: .default_branch}'
└ {"default_branch":"main","name":"data-archive-1","size_gib":76.31462860107422,"size_kb":80021688
  }

────────────────────────────────────────────────────────────────────────────────────────────────────

• Yes. The publisher automatically creates ufo-files/data-archive-2 when either:

- data-archive-1 reaches the configured 90 GiB threshold, or
- GitHub rejects a push because the repository is above quota.

The current warning is not a rejection. GitHub reports data-archive-1 at approximately 76.3 GiB,
so this batch will continue there. Any in-flight batch rejected for quota will be reset locally
and replayed automatically into data-archive-2.

────────────────────────────────────────────────────────────────────────────────────────────────────

• Stopping all background terminals.


› our archived count on the table went from 95k to 41k. why?


• I’m tracing the count calculation and comparing it with the current archive manifests. A drop that
large is almost certainly a definition or cache-path regression, not 54,000 deleted originals, and
I’m verifying which records stopped being counted.

• Ran rg -n "sum_archived_counts|archived_count_from_manifest|publisher.*archived|TOTAL" scripts/
│ update_epaper_status.py && git log --oneline --all -- scripts/update_epaper_status.py | head
│ -25 && git log -p -5 -- scripts/update_epaper_status.py | rg -n "archived|TOTAL|cache|count" |
│ … +1 lines
└ 217:        help="Show Git publisher progress with percent archived as the final column.",
  671:def publisher_source_counts(source: Path, archived_paths: set[str], current_paths: set[str]
  … +89 lines (ctrl + t to view transcript)
  390:             "site": "TOTAL",
  395:             "archived": format_count(total_archived),

• Explored
└ Read update_epaper_status.py

────────────────────────────────────────────────────────────────────────────────────────────────────

• I found the regression. The stale-status reconciliation I just added also replaced each cached
filesystem count with the smaller manifest-record count. NARA’s manifest is not a complete
inventory of all extracted files, so that collapsed the total from roughly 95k to 41k. No archive
files were deleted; I’m removing that count overwrite now and adding a regression test.

• Edited 2 files (+1 -1)
└ /private/tmp/ufo-files-agents-current/scripts/tests/test_update_epaper_status.py (+1 -0)
  105          self.assertEqual(reconciled["last_downloaded"], "2026-07-19T14:05:01Z")
  106 +        self.assertEqual(reconciled["archived"], "11")
  107

└ /private/tmp/ufo-files-agents-current/scripts/update_epaper_status.py (+0 -1)
  1194      reconciled["last_checked"] = manifest_checked
  1195 -    reconciled["archived"] = format_count(archived_count_from_manifest(manifest, archive_d
        ir))
  1195      reconciled["last_downloaded"] = last_downloaded_from_manifest(manifest, archive_dir)

• Ran /private/tmp/ufo-agents-test-venv/bin/python -m unittest
│ scripts.tests.test_update_epaper_status -v && python3 -m py_compile scripts/
│ update_epaper_status.py && git diff --check && git add scripts/update_epaper_status.py
│ … +2 lines
└ test_active_source_percentage_has_staging_arrow
  (scripts.tests.test_update_epaper_status.PublisherEpaperStatusTests.test_active_source_percentag
  … +35 lines (ctrl + t to view transcript)
  fatal: unable to access 'https://github.com/ufo-files/agents.git/': Could not resolve host:
  github.com

• Ran git push origin master
└ To https://github.com/ufo-files/agents.git
     0c882e1..cf077ab  master -> master

• Explored
└ Search def publisher_filesystem_paths|PUBLISHER_FILESYSTEM in update_epaper_status.py
  Read update_epaper_status.py

────────────────────────────────────────────────────────────────────────────────────────────────────

• That was my regression. The status reconciliation replaced complete filesystem inventory counts
with smaller manifest-record counts, primarily undercounting NARA. No files were deleted.

Fixed and pushed as cf077ab; all 20 tests pass. Pull and reopen the table:

ssh -t -i ~/.ssh/ufo_agent_pi_ed25519 ufo-agent@192.168.0.131 'cd /home/ufo-agent/agents && git
pull --ff-only origin master && ./scripts/update_epaper_status.py --status-table'

The archived total should return to the roughly 95k inventory count.

─ Worked for 1m 17s ────────────────────────────────────────────────────────────────────────────────


› UGH I WANT TO MONITOR IT
+--------------------------+--------------+--------------+-----------------+----------+
| SITE                     | STATUS       | LAST CHECKED | LAST DOWNLOADED | ARCHIVED |
+--------------------------+--------------+--------------+-----------------+----------+
| fbi.gov                  | up-to-date   | 07/19 02:07  | -               | 16       |
| archives.gov             | up-to-date   | 07/19 06:17  | 07/11 06:18     | 84,137   |
| dpiarchive.com           | up-to-date   | 07/19 14:32  | 07/10 16:23     | 3,225    |
| drstevengreer.com        | up-to-date   | 07/19 14:42  | -               | 143      |
| nsa.gov                  | up-to-date   | 07/19 16:52  | 07/08 13:35     | 159      |
| energy.gov               | up-to-date   | 07/19 18:57  | 07/08 13:57     | 2        |
| aaro.mil                 | up-to-date   | 07/20 00:53  | 07/08 14:05     | 11       |
| theblackvault.com        | up-to-date   | 07/19 08:38  | -               | 4,370    |
| American Alchemy         | up-to-date   | 07/19 04:12  | -               | 132      |
| war.gov/ufo              | up-to-date   | 07/19 10:27  | -               | 302      |
+--------------------------+--------------+--------------+-----------------+----------+
| TOTAL                    |              |              |                 | 92,497   |
+--------------------------+--------------+--------------+-----------------+----------+
Connection to 192.168.0.131 closed.
glennsorrentino@Glenns-MacBook-Pro hushline %


• Use watch so the table stays open and refreshes every 30 seconds:

ssh -t -i ~/.ssh/ufo_agent_pi_ed25519 ufo-agent@192.168.0.131 'cd /home/ufo-agent/agents &&
TERM=xterm watch -d -n 30 ./scripts/update_epaper_status.py --status-table'

Press Ctrl-C to exit.


› please update the readmes of all of the data-archive repos. include a table on each with all of
the reposa, their folders, and links. make the readmes helpful.


• I’ll inventory every ufo-files repository in the archive family first, including current shard
contents and folder roots, then update each README with one consistent cross-repository directory.
I’ll preserve repository-specific purpose and avoid implying that a not-yet-created shard already
exists.

• Ran gh api users/ufo-files/repos --paginate --jq '.[] | select(.name | startswith("data-archive"))
│ | [.name, .html_url, .description, .default_branch, .private, .size] | @tsv'
└ data-archive    https://github.com/ufo-files/data-archive    Browsable UFO Files source archive
  preserving original paths    main    false    108257405
  … +2 lines (ctrl + t to view transcript)
  data-archive-2    https://github.com/ufo-files/data-archive-2    Original source files for the
  UFO Files public archive.    main    false    0

• Ran gh repo list ufo-files --limit 200 --json
│ name,url,description,defaultBranchRef,isPrivate,diskUsage --jq '.[] | select(.name |
│ startswith("data-archive")) |
│ … +1 lines
└ data-archive-2    https://github.com/ufo-files/data-archive-2    Original source files for the
  UFO Files public archive.    main    false    0
  … +2 lines (ctrl + t to view transcript)
  data-archive    https://github.com/ufo-files/data-archive    Browsable UFO Files source archive
  preserving original paths    main    false    108257405

• Ran gh api graphql -f query='query { a: repository(owner:"ufo-files", name:"data-archive")
│ { object(expression:"main:") { ... on Tree { entries { name type } } } } b:
│ repository(owner:"ufo-files", name:"data-archive-1") { object(expression:"main:") { ... on
│ … +5 lines
└ {"data-archive":
  [".github","AARO-UAP-Records","American-Alchemy","Black-Vault-UFO","DOE-NNSA-UAP-UFO","DPIArchiv
  e","FBI-Vault-UFO","Legacy-Documents","NSA-UFO-FOIA","National-Archives-UAP-Bulk","Steven-Greer-
  Document-Library","War-Gov-PURSUE","wikileaks"],"data-archive-1":
  [".github","National-Archives-UAP-Bulk"],"data-archive-2":["National-Archives-UAP-Bulk"]}

• Ran gh api repos/ufo-files/data-archive/contents/README.md -H 'Accept: application/
│ vnd.github.raw+json'
└ # UFO Files Data Archive

  … +4 lines (ctrl + t to view transcript)

  Browsable UFO Files source archive preserving original paths.

• Ran gh api repos/ufo-files/data-archive-1/contents/README.md -H 'Accept: application/
│ vnd.github.raw+json'
└ # UFO Files Data Archive 1

  … +7 lines (ctrl + t to view transcript)
  This is shard 1 of the public archive. The live count covers `data-archive`,
  this repository, and future repositories named `data-archive-N`.

• Ran gh api repos/ufo-files/data-archive-2/contents/README.md -H 'Accept: application/
│ vnd.github.raw+json'
└ # data-archive-2
  Original source files for the UFO Files public archive.

────────────────────────────────────────────────────────────────────────────────────────────────────

• There are now three public shards: the base repository, shard 1, and the newly created shard 2.
Their current layouts differ, so I’m making the directory table explicit: the base holds all
source families, while shards 1 and 2 currently hold NARA material; all three will share the same
live total badge and navigation.

• Ran rm -rf /private/tmp/ufo-data-archive-readmes && mkdir -p /private/tmp/ufo-data-archive-readmes
│ && git clone --filter=blob:none --depth=1 --sparse
│ https://github.com/ufo-files/data-archive.git
│ … +1 lines
└ (no output)

• Ran git clone --filter=blob:none --depth=1 --sparse
│ https://github.com/ufo-files/data-archive-1.git
│ /private/tmp/ufo-data-archive-readmes/data-archive-1
└ (no output)

• Ran git clone --filter=blob:none --depth=1 --sparse
│ https://github.com/ufo-files/data-archive-2.git
│ /private/tmp/ufo-data-archive-readmes/data-archive-2
└ (no output)

• Ran find /private/tmp/ufo-data-archive-readmes -maxdepth 2 -name AGENTS.md -o -name README.md
│ -print && git -C /private/tmp/ufo-data-archive-readmes/data-archive status --short --branch &&
│ git -C /private/tmp/ufo-data-archive-readmes/data-archive-1 status --short --branch && git
│ … +1 lines
└ /private/tmp/ufo-data-archive-readmes/data-archive-2/README.md
  /private/tmp/ufo-data-archive-readmes/data-archive/README.md
  … +2 lines (ctrl + t to view transcript)
  ## main...origin/main
  ## main...origin/main

────────────────────────────────────────────────────────────────────────────────────────────────────

• I’m editing the three README files now. The shared structure will explain sharding, link every
current top-level archive folder in every repository, point all badges to the canonical cross-
shard count, and distinguish preserved source material from derived corpus data.

• Added /private/tmp/ufo-data-archive-readmes/data-archive/README.md (+49 -0)
   1 +# UFO Files Data Archive
   2 +
   3 +[![Live archive count](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githu
      busercontent.com%2Fufo-files%2Fdata-archive-1%2Farchive-count%2Farchive-count.json&query=%24
      .count&label=archived%20files&color=111111)](https://raw.githubusercontent.com/ufo-files/dat
      a-archive-1/archive-count/archive-count.json)
   4 +[![Archive shards](https://img.shields.io/badge/archive%20shards-3-111111)](#archive-directo
      ry)
   5 +
   6 +The UFO Files Data Archive preserves original public source material used by the
   7 +[UFO Files](https://ufo-files.app) project. Files retain their source-relative
   8 +paths so they can be traced back to the collection that supplied them.
   9 +
  10 +The archive is split across multiple GitHub repositories to keep it browsable
  11 +as it grows. A source folder may appear in more than one shard; those folders
  12 +contain different portions of the same collection. Use the directory below to
  13 +navigate the complete public archive.
  14 +
  15 +## Archive Directory
  16 +
  17 +| Repository | Purpose | Top-level archive folders |
  18 +| --- | --- | --- |
  19 +| **[`data-archive`](https://github.com/ufo-files/data-archive)** | Base shard and broad sou
      rce index | [`AARO-UAP-Records`](https://github.com/ufo-files/data-archive/tree/main/AARO-UA
      P-Records)<br>[`American-Alchemy`](https://github.com/ufo-files/data-archive/tree/main/Ameri
      can-Alchemy)<br>[`Black-Vault-UFO`](https://github.com/ufo-files/data-archive/tree/main/Blac
      k-Vault-UFO)<br>[`DOE-NNSA-UAP-UFO`](https://github.com/ufo-files/data-archive/tree/main/DOE
      -NNSA-UAP-UFO)<br>[`DPIArchive`](https://github.com/ufo-files/data-archive/tree/main/DPIArch
      ive)<br>[`FBI-Vault-UFO`](https://github.com/ufo-files/data-archive/tree/main/FBI-Vault-UFO)
      <br>[`Legacy-Documents`](https://github.com/ufo-files/data-archive/tree/main/Legacy-Document
      s)<br>[`NSA-UFO-FOIA`](https://github.com/ufo-files/data-archive/tree/main/NSA-UFO-FOIA)<br>
      [`National-Archives-UAP-Bulk`](https://github.com/ufo-files/data-archive/tree/main/National-
      Archives-UAP-Bulk)<br>[`Steven-Greer-Document-Library`](https://github.com/ufo-files/data-ar
      chive/tree/main/Steven-Greer-Document-Library)<br>[`War-Gov-PURSUE`](https://github.com/ufo-
      files/data-archive/tree/main/War-Gov-PURSUE)<br>[`wikileaks`](https://github.com/ufo-files/d
      ata-archive/tree/main/wikileaks) |
  20 +| [`data-archive-1`](https://github.com/ufo-files/data-archive-1) | Archive shard 1 and cano
      nical live-count publisher | [`National-Archives-UAP-Bulk`](https://github.com/ufo-files/dat
      a-archive-1/tree/main/National-Archives-UAP-Bulk) |
  21 +| [`data-archive-2`](https://github.com/ufo-files/data-archive-2) | Archive shard 2 | [`Nati
      onal-Archives-UAP-Bulk`](https://github.com/ufo-files/data-archive-2/tree/main/National-Arch
      ives-UAP-Bulk) |
  22 +
  23 +## What Is Preserved
  24 +
  25 +- Original PDFs, images, videos, audio, and other downloaded source files
  26 +- Source-specific folder names and relative paths
  27 +- Manifests, checksums, and collection metadata where supplied by the archiver
  28 +- Git history showing when files entered the public archive
  29 +
  30 +ZIP packages, temporary files, processing state, and derived OCR or transcript
  31 +output are excluded from the public source-file count. The live badge is built
  32 +from the union of all numbered archive shards and deduplicates matching relative
  33 +paths.
  34 +
  35 +## Finding Derived Data
  36 +
  37 +This repository preserves source files. Searchable OCR, transcripts,
  38 +thumbnails, and normalized corpus records live in
  39 +[`ufo-files/data`](https://github.com/ufo-files/data). Explore relationships
  40 +derived from that corpus in the
  41 +[`relationship-graph`](https://github.com/ufo-files/relationship-graph).
  42 +
  43 +## Provenance
  44 +
  45 +An archived file records what a source published; its presence does not verify
  46 +the claims it contains or imply endorsement by UFO Files. Source material may
  47 +include disputed, historical, testimonial, journalistic, or government records.
  48 +Consult each file's collection metadata and original publisher when evaluating
  49 +provenance.

• Added /private/tmp/ufo-data-archive-readmes/data-archive-1/README.md (+55 -0)
   1 +# UFO Files Data Archive 1
   2 +
   3 +[![Live archive count](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githu
      busercontent.com%2Fufo-files%2Fdata-archive-1%2Farchive-count%2Farchive-count.json&query=%24
      .count&label=archived%20files&color=111111)](https://raw.githubusercontent.com/ufo-files/dat
      a-archive-1/archive-count/archive-count.json)
   4 +[![Archive shards](https://img.shields.io/badge/archive%20shards-3-111111)](#archive-directo
      ry)
   5 +
   6 +This is shard 1 of the [UFO Files](https://ufo-files.app) public source archive.
   7 +It preserves original source material while retaining the source-relative paths
   8 +used across the archive.
   9 +
  10 +The archive is split across multiple GitHub repositories to keep it browsable
  11 +as it grows. A source folder may appear in more than one shard; those folders
  12 +contain different portions of the same collection. Use the directory below to
  13 +navigate the complete public archive.
  14 +
  15 +## Archive Directory
  16 +
  17 +| Repository | Purpose | Top-level archive folders |
  18 +| --- | --- | --- |
  19 +| [`data-archive`](https://github.com/ufo-files/data-archive) | Base shard and broad source
      index | [`AARO-UAP-Records`](https://github.com/ufo-files/data-archive/tree/main/AARO-UAP-Re
      cords)<br>[`American-Alchemy`](https://github.com/ufo-files/data-archive/tree/main/American-
      Alchemy)<br>[`Black-Vault-UFO`](https://github.com/ufo-files/data-archive/tree/main/Black-Va
      ult-UFO)<br>[`DOE-NNSA-UAP-UFO`](https://github.com/ufo-files/data-archive/tree/main/DOE-NNS
      A-UAP-UFO)<br>[`DPIArchive`](https://github.com/ufo-files/data-archive/tree/main/DPIArchive)
      <br>[`FBI-Vault-UFO`](https://github.com/ufo-files/data-archive/tree/main/FBI-Vault-UFO)<br>
      [`Legacy-Documents`](https://github.com/ufo-files/data-archive/tree/main/Legacy-Documents)<b
      r>[`NSA-UFO-FOIA`](https://github.com/ufo-files/data-archive/tree/main/NSA-UFO-FOIA)<br>[`Na
      tional-Archives-UAP-Bulk`](https://github.com/ufo-files/data-archive/tree/main/National-Arch
      ives-UAP-Bulk)<br>[`Steven-Greer-Document-Library`](https://github.com/ufo-files/data-archiv
      e/tree/main/Steven-Greer-Document-Library)<br>[`War-Gov-PURSUE`](https://github.com/ufo-file
      s/data-archive/tree/main/War-Gov-PURSUE)<br>[`wikileaks`](https://github.com/ufo-files/data-
      archive/tree/main/wikileaks) |
  20 +| **[`data-archive-1`](https://github.com/ufo-files/data-archive-1)** | Archive shard 1 and
      canonical live-count publisher | [`National-Archives-UAP-Bulk`](https://github.com/ufo-files
      /data-archive-1/tree/main/National-Archives-UAP-Bulk) |
  21 +| [`data-archive-2`](https://github.com/ufo-files/data-archive-2) | Archive shard 2 | [`Nati
      onal-Archives-UAP-Bulk`](https://github.com/ufo-files/data-archive-2/tree/main/National-Arch
      ives-UAP-Bulk) |
  22 +
  23 +## Live Count
  24 +
  25 +The [`archive-count` branch](https://github.com/ufo-files/data-archive-1/tree/archive-count)
  26 +publishes the canonical machine-readable
  27 +[`archive-count.json`](https://raw.githubusercontent.com/ufo-files/data-archive-1/archive-co
      unt/archive-count.json).
  28 +It inventories the union of every numbered archive shard and deduplicates
  29 +matching relative paths.
  30 +
  31 +ZIP packages, temporary files, processing state, and derived OCR or transcript
  32 +output are excluded from the public source-file count.
  33 +
  34 +## What Is Preserved
  35 +
  36 +- Original PDFs, images, videos, audio, and other downloaded source files
  37 +- Source-specific folder names and relative paths
  38 +- Manifests, checksums, and collection metadata where supplied by the archiver
  39 +- Git history showing when files entered the public archive
  40 +
  41 +## Finding Derived Data
  42 +
  43 +This repository preserves source files. Searchable OCR, transcripts,
  44 +thumbnails, and normalized corpus records live in
  45 +[`ufo-files/data`](https://github.com/ufo-files/data). Explore relationships
  46 +derived from that corpus in the
  47 +[`relationship-graph`](https://github.com/ufo-files/relationship-graph).
  48 +
  49 +## Provenance
  50 +
  51 +An archived file records what a source published; its presence does not verify
  52 +the claims it contains or imply endorsement by UFO Files. Source material may
  53 +include disputed, historical, testimonial, journalistic, or government records.
  54 +Consult each file's collection metadata and original publisher when evaluating
  55 +provenance.

• Added /private/tmp/ufo-data-archive-readmes/data-archive-2/README.md (+49 -0)
   1 +# UFO Files Data Archive 2
   2 +
   3 +[![Live archive count](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githu
      busercontent.com%2Fufo-files%2Fdata-archive-1%2Farchive-count%2Farchive-count.json&query=%24
      .count&label=archived%20files&color=111111)](https://raw.githubusercontent.com/ufo-files/dat
      a-archive-1/archive-count/archive-count.json)
   4 +[![Archive shards](https://img.shields.io/badge/archive%20shards-3-111111)](#archive-directo
      ry)
   5 +
   6 +This is shard 2 of the [UFO Files](https://ufo-files.app) public source archive.
   7 +It preserves original source material while retaining the source-relative paths
   8 +used across the archive.
   9 +
  10 +The archive is split across multiple GitHub repositories to keep it browsable
  11 +as it grows. A source folder may appear in more than one shard; those folders
  12 +contain different portions of the same collection. Use the directory below to
  13 +navigate the complete public archive.
  14 +
  15 +## Archive Directory
  16 +
  17 +| Repository | Purpose | Top-level archive folders |
  18 +| --- | --- | --- |
  19 +| [`data-archive`](https://github.com/ufo-files/data-archive) | Base shard and broad source
      index | [`AARO-UAP-Records`](https://github.com/ufo-files/data-archive/tree/main/AARO-UAP-Re
      cords)<br>[`American-Alchemy`](https://github.com/ufo-files/data-archive/tree/main/American-
      Alchemy)<br>[`Black-Vault-UFO`](https://github.com/ufo-files/data-archive/tree/main/Black-Va
      ult-UFO)<br>[`DOE-NNSA-UAP-UFO`](https://github.com/ufo-files/data-archive/tree/main/DOE-NNS
      A-UAP-UFO)<br>[`DPIArchive`](https://github.com/ufo-files/data-archive/tree/main/DPIArchive)
      <br>[`FBI-Vault-UFO`](https://github.com/ufo-files/data-archive/tree/main/FBI-Vault-UFO)<br>
      [`Legacy-Documents`](https://github.com/ufo-files/data-archive/tree/main/Legacy-Documents)<b
      r>[`NSA-UFO-FOIA`](https://github.com/ufo-files/data-archive/tree/main/NSA-UFO-FOIA)<br>[`Na
      tional-Archives-UAP-Bulk`](https://github.com/ufo-files/data-archive/tree/main/National-Arch
      ives-UAP-Bulk)<br>[`Steven-Greer-Document-Library`](https://github.com/ufo-files/data-archiv
      e/tree/main/Steven-Greer-Document-Library)<br>[`War-Gov-PURSUE`](https://github.com/ufo-file
      s/data-archive/tree/main/War-Gov-PURSUE)<br>[`wikileaks`](https://github.com/ufo-files/data-
      archive/tree/main/wikileaks) |
  20 +| [`data-archive-1`](https://github.com/ufo-files/data-archive-1) | Archive shard 1 and cano
      nical live-count publisher | [`National-Archives-UAP-Bulk`](https://github.com/ufo-files/dat
      a-archive-1/tree/main/National-Archives-UAP-Bulk) |
  21 +| **[`data-archive-2`](https://github.com/ufo-files/data-archive-2)** | Archive shard 2 | [`
      National-Archives-UAP-Bulk`](https://github.com/ufo-files/data-archive-2/tree/main/National-
      Archives-UAP-Bulk) |
  22 +
  23 +## What Is Preserved
  24 +
  25 +- Original PDFs, images, videos, audio, and other downloaded source files
  26 +- Source-specific folder names and relative paths
  27 +- Manifests, checksums, and collection metadata where supplied by the archiver
  28 +- Git history showing when files entered the public archive
  29 +
  30 +ZIP packages, temporary files, processing state, and derived OCR or transcript
  31 +output are excluded from the public source-file count. The live badge is built
  32 +from the union of all numbered archive shards and deduplicates matching relative
  33 +paths.
  34 +
  35 +## Finding Derived Data
  36 +
  37 +This repository preserves source files. Searchable OCR, transcripts,
  38 +thumbnails, and normalized corpus records live in
  39 +[`ufo-files/data`](https://github.com/ufo-files/data). Explore relationships
  40 +derived from that corpus in the
  41 +[`relationship-graph`](https://github.com/ufo-files/relationship-graph).
  42 +
  43 +## Provenance
  44 +
  45 +An archived file records what a source published; its presence does not verify
  46 +the claims it contains or imply endorsement by UFO Files. Source material may
  47 +include disputed, historical, testimonial, journalistic, or government records.
  48 +Consult each file's collection metadata and original publisher when evaluating
  49 +provenance.

────────────────────────────────────────────────────────────────────────────────────────────────────

• The README content is in place across all three clones. I’m validating the Markdown diffs and then
pushing each repository separately, since shard 1 is actively receiving publisher commits and may
need a rebase between the README commit and push.

• Ran git diff --check && git diff --stat && sed -n '1,180p' README.md
└  README.md | 48 ++++++++++++++++++++++++++++++++++++++++++++++--
   1 file changed, 46 insertions(+), 2 deletions(-)
  … +50 lines (ctrl + t to view transcript)
  Consult each file's collection metadata and original publisher when evaluating
  provenance.

• Ran git diff --check && git diff --stat
└  README.md | 53 ++++++++++++++++++++++++++++++++++++++++++++++++++---
   1 file changed, 50 insertions(+), 3 deletions(-)

• Ran git diff --check && git diff --stat
└  README.md | 51 +++++++++++++++++++++++++++++++++++++++++++++++++--
   1 file changed, 49 insertions(+), 2 deletions(-)

• Ran git config user.name "ufo-files" && git config user.email
│ "297273897+ufo-files@users.noreply.github.com" && git add README.md && git commit -m "Document
│ public archive shards" && git push origin main
└ remote: error: Repository is above its size quota. Contact GitHub Support for further
  assistance.
  To https://github.com/ufo-files/data-archive.git
   ! [remote rejected] main -> main (pre-receive hook declined)
  error: failed to push some refs to 'https://github.com/ufo-files/data-archive.git'

────────────────────────────────────────────────────────────────────────────────────────────────────

• data-archive is already above GitHub’s size quota, so GitHub rejected even this README-only Git
push. I’m switching that one to GitHub’s contents API, which can sometimes update repository
metadata files without transporting the oversized Git history; shards 1 and 2 can use normal
pushes.

• Ran content=$(base64 < README.md | tr -d '\n')
│ sha=$(gh api repos/ufo-files/data-archive/contents/README.md --jq .sha)
│ gh api --method PUT repos/ufo-files/data-archive/contents/README.md -f message='Document public
│ … +1 lines
└ error connecting to api.github.com
  check your internet connection or https://githubstatus.com
  error connecting to api.github.com
  check your internet connection or https://githubstatus.com

✔ You approved codex to run content=$(base64 < README.md | tr -d '\n') ... this time

• Ran content=$(base64 < README.md | tr -d '\n')
│ sha=$(gh api repos/ufo-files/data-archive/contents/README.md --jq .sha)
│ gh api --method PUT repos/ufo-files/data-archive/contents/README.md -f message='Document public
│ … +1 lines
└ {"message":"Repository is above its size quota.","documentation_url":"https://docs.github.com/
  rest/repos/contents#create-or-update-file-contents","status":"403"}gh: Repository is above its
  size quota. (HTTP 403)

• Ran gh api repos/ufo-files/data-archive/git/matching-refs/heads --jq '.[].ref'
└ refs/heads/archive-count
  refs/heads/main

• Ran git config user.name "ufo-files" && git config user.email
│ "297273897+ufo-files@users.noreply.github.com" && git add README.md && git commit -m "Document
│ public archive shards" && git pull --rebase origin main && git push origin main
└ From https://github.com/ufo-files/data-archive-1
   * branch            main       -> FETCH_HEAD
  … +2 lines (ctrl + t to view transcript)
  To https://github.com/ufo-files/data-archive-1.git
     201ae2d..9bc86e3  main -> main

• Ran git config user.name "ufo-files" && git config user.email
│ "297273897+ufo-files@users.noreply.github.com" && git add README.md && git commit -m "Document
│ public archive shards" && git pull --rebase origin main && git push origin main
└ From https://github.com/ufo-files/data-archive-2
   * branch            main       -> FETCH_HEAD
  … +2 lines (ctrl + t to view transcript)
  To https://github.com/ufo-files/data-archive-2.git
     3640cb9..1b675a6  main -> main

────────────────────────────────────────────────────────────────────────────────────────────────────

• Shards 1 and 2 are updated. The base repository rejected both normal Git and Contents API updates
because it is already above quota. I’m making one final non-destructive attempt through GitHub’s
low-level Git object API; if GitHub blocks that too, the base README cannot change until the
oversized repository is migrated or GitHub Support lifts the write block.

✔ You approved codex to run content=$(base64 < README.md | tr -d '\n') ... this time

• Ran content=$(base64 < README.md | tr -d '\n')
│ gh api --method POST repos/ufo-files/data-archive/git/blobs -f content="$content" -f
│ encoding=base64 --jq .sha
└ gh: Repository is above its size quota. (HTTP 403)
  {"message":"Repository is above its size quota.","documentation_url":"https://docs.github.com/
  rest/git/blobs#create-a-blob","status":"403"}

• Ran gh api repos/ufo-files/data-archive-1/contents/README.md -H 'Accept: application/
│ vnd.github.raw+json'
└ # UFO Files Data Archive 1

  … +54 lines (ctrl + t to view transcript)
  Consult each file's collection metadata and original publisher when evaluating
  provenance.

• Ran gh api repos/ufo-files/data-archive-2/contents/README.md -H 'Accept: application/
│ vnd.github.raw+json'
└ # UFO Files Data Archive 2

  … +48 lines (ctrl + t to view transcript)
  Consult each file's collection metadata and original publisher when evaluating
  provenance.

────────────────────────────────────────────────────────────────────────────────────────────────────

• Updated and verified:

- data-archive-1 (https://github.com/ufo-files/data-archive-1) at 9bc86e3
- data-archive-2 (https://github.com/ufo-files/data-archive-2) at 1b675a6

Each now includes the shared live-count badge, archive explanation, complete repository/folder/
link table, derived-data guidance, and provenance notes.

The base data-archive (https://github.com/ufo-files/data-archive) update is blocked by GitHub
because it is approximately 103.2 GiB and above quota. Git push, Contents API, and low-level Git
API all returned HTTP 403. Its README change is prepared locally, but GitHub will not accept any
new object until the repository is migrated/recreated or Support removes the write block.

─ Worked for 7m 53s ────────────────────────────────────────────────────────────────────────────────


› what aout data-archive?


• data-archive is not updated. GitHub has hard-locked it at roughly 103.2 GiB. All three methods
failed with “Repository is above its size quota”:

- Normal Git push
- GitHub Contents API
- Low-level Git blob API

The proper fix is to migrate its unique files into numbered shards, verify 100% cross-shard
coverage, then recreate data-archive as a lightweight index repository. Recreating it before that
verification risks losing its unique archived files.


› huh? you couldnt edit the readme?


• Correct. GitHub refuses all new Git objects in data-archive, including a tiny README edit, because
the repository exceeds its size quota.

The README is prepared locally, but every upload method returned HTTP 403:

Repository is above its size quota.

This is a GitHub-side write lock, not a README or permissions problem.


› i can edit it. give me the markdown


• # UFO Files Data Archive

Live archive count
(https://raw.githubusercontent.com/ufo-files/data-archive-1/archive-count/archive-count.json)
Archive shards (#archive-directory)

The UFO Files Data Archive preserves original public source material used by the
UFO Files (https://ufo-files.app) project. Files retain their source-relative
paths so they can be traced back to the collection that supplied them.

The archive is split across multiple GitHub repositories to keep it browsable
as it grows. A source folder may appear in more than one shard; those folders
contain different portions of the same collection.

## Archive Directory

 Repository                 data-archive (https://github.com/ufo-files/data-archive)
 Purpose                    Base shard and broad source index
 Top-level archive folders  AARO-UAP-Records (https://github.com/ufo-files/data-archive/tree/main/
                            AARO-UAP-Records)<br>American-Alchemy (https://github.com/ufo-files/
                            data-archive/tree/main/American-Alchemy)<br>Black-Vault-UFO (https://
                            github.com/ufo-files/data-archive/tree/main/Black-Vault-UFO)<br>DOE-
                            NNSA-UAP-UFO (https://github.com/ufo-files/data-archive/tree/main/DOE-
                            NNSA-UAP-UFO)<br>DPIArchive (https://github.com/ufo-files/data-
                            archive/tree/main/DPIArchive)<br>FBI-Vault-UFO (https://github.com/
                            ufo-files/data-archive/tree/main/FBI-Vault-UFO)<br>Legacy-Documents
                            (https://github.com/ufo-files/data-archive/tree/main/Legacy-
                            Documents)<br>NSA-UFO-FOIA (https://github.com/ufo-files/data-archive/
                            tree/main/NSA-UFO-FOIA)<br>National-Archives-UAP-Bulk (https://
                            github.com/ufo-files/data-archive/tree/main/National-Archives-UAP-
                            Bulk)<br>Steven-Greer-Document-Library (https://github.com/ufo-files/
                            data-archive/tree/main/Steven-Greer-Document-Library)<br>War-Gov-
                            PURSUE (https://github.com/ufo-files/data-archive/tree/main/War-Gov-
                            PURSUE)<br>wikileaks (https://github.com/ufo-files/data-archive/tree/
                            main/wikileaks)
──────────────────────────────────────────────────────────────────────────────────────────────────
 Repository                 data-archive-1 (https://github.com/ufo-files/data-archive-1)
 Purpose                    Archive shard 1 and canonical live-count publisher
 Top-level archive folders  National-Archives-UAP-Bulk (https://github.com/ufo-files/data-archive-
                            1/tree/main/National-Archives-UAP-Bulk)
──────────────────────────────────────────────────────────────────────────────────────────────────
 Repository                 data-archive-2 (https://github.com/ufo-files/data-archive-2)
 Purpose                    Archive shard 2
 Top-level archive folders  National-Archives-UAP-Bulk (https://github.com/ufo-files/data-archive-
                            2/tree/main/National-Archives-UAP-Bulk)

## What Is Preserved

- Original PDFs, images, videos, audio, and other downloaded source files
- Source-specific folder names and relative paths
- Manifests, checksums, and collection metadata where supplied by the archiver
- Git history showing when files entered the public archive

ZIP packages, temporary files, processing state, and derived OCR or transcript
output are excluded from the public source-file count. The live badge is built
from the union of all numbered archive shards and deduplicates matching relative
paths.

## Finding Derived Data

Searchable OCR, transcripts, thumbnails, and normalized corpus records live in
ufo-files/data (https://github.com/ufo-files/data). Explore relationships
derived from that corpus in the
relationship-graph (https://github.com/ufo-files/relationship-graph).

## Provenance

An archived file records what a source published. Its presence does not verify
the claims it contains or imply endorsement by UFO Files. Source material may
include disputed, historical, testimonial, journalistic, or government records.
Consult each file's collection metadata and original publisher when evaluating
provenance.


› that doesnt match the others


• You're right. The base version omitted the Live Count section. Use this version:

# UFO Files Data Archive

Live archive count
(https://raw.githubusercontent.com/ufo-files/data-archive-1/archive-count/archive-count.json)
Archive shards (#archive-directory)

This is the base shard of the UFO Files (https://ufo-files.app) public source
archive. It preserves original source material while retaining the
source-relative paths used across the archive.

The archive is split across multiple GitHub repositories to keep it browsable
as it grows. A source folder may appear in more than one shard; those folders
contain different portions of the same collection. Use the directory below to
navigate the complete public archive.

## Archive Directory

 Repository                 data-archive (https://github.com/ufo-files/data-archive)
 Purpose                    Base shard and broad source index
 Top-level archive folders  AARO-UAP-Records (https://github.com/ufo-files/data-archive/tree/main/
                            AARO-UAP-Records)<br>American-Alchemy (https://github.com/ufo-files/
                            data-archive/tree/main/American-Alchemy)<br>Black-Vault-UFO (https://
                            github.com/ufo-files/data-archive/tree/main/Black-Vault-UFO)<br>DOE-
                            NNSA-UAP-UFO (https://github.com/ufo-files/data-archive/tree/main/DOE-
                            NNSA-UAP-UFO)<br>DPIArchive (https://github.com/ufo-files/data-
                            archive/tree/main/DPIArchive)<br>FBI-Vault-UFO (https://github.com/
                            ufo-files/data-archive/tree/main/FBI-Vault-UFO)<br>Legacy-Documents
                            (https://github.com/ufo-files/data-archive/tree/main/Legacy-
                            Documents)<br>NSA-UFO-FOIA (https://github.com/ufo-files/data-archive/
                            tree/main/NSA-UFO-FOIA)<br>National-Archives-UAP-Bulk (https://
                            github.com/ufo-files/data-archive/tree/main/National-Archives-UAP-
                            Bulk)<br>Steven-Greer-Document-Library (https://github.com/ufo-files/
                            data-archive/tree/main/Steven-Greer-Document-Library)<br>War-Gov-
                            PURSUE (https://github.com/ufo-files/data-archive/tree/main/War-Gov-
                            PURSUE)<br>wikileaks (https://github.com/ufo-files/data-archive/tree/
                            main/wikileaks)
──────────────────────────────────────────────────────────────────────────────────────────────────
 Repository                 data-archive-1 (https://github.com/ufo-files/data-archive-1)
 Purpose                    Archive shard 1 and canonical live-count publisher
 Top-level archive folders  National-Archives-UAP-Bulk (https://github.com/ufo-files/data-archive-
                            1/tree/main/National-Archives-UAP-Bulk)
──────────────────────────────────────────────────────────────────────────────────────────────────
 Repository                 data-archive-2 (https://github.com/ufo-files/data-archive-2)
 Purpose                    Archive shard 2
 Top-level archive folders  National-Archives-UAP-Bulk (https://github.com/ufo-files/data-archive-
                            2/tree/main/National-Archives-UAP-Bulk)

## Live Count

The archive-count branch (https://github.com/ufo-files/data-archive-1/tree/archive-count)
publishes the canonical machine-readable
archive-count.json
(https://raw.githubusercontent.com/ufo-files/data-archive-1/archive-count/archive-count.json).
It inventories the union of every numbered archive shard and deduplicates
matching relative paths.

ZIP packages, temporary files, processing state, and derived OCR or transcript
output are excluded from the public source-file count.

## What Is Preserved

- Original PDFs, images, videos, audio, and other downloaded source files
- Source-specific folder names and relative paths
- Manifests, checksums, and collection metadata where supplied by the archiver
- Git history showing when files entered the public archive

## Finding Derived Data

This repository preserves source files. Searchable OCR, transcripts,
thumbnails, and normalized corpus records live in
ufo-files/data (https://github.com/ufo-files/data). Explore relationships
derived from that corpus in the
relationship-graph (https://github.com/ufo-files/relationship-graph).

## Provenance

An archived file records what a source published; its presence does not verify
the claims it contains or imply endorsement by UFO Files. Source material may
include disputed, historical, testimonial, journalistic, or government records.
Consult each file's collection metadata and original publisher when evaluating
provenance.
