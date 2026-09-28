# HubSpot adapter: portal discovery and the pre-sync check

HubSpot is supported **generically, with native schema discovery**
(`references/platform-support.md`). Every portal is different: custom properties, custom
objects, picklist options, required fields. So before the engine writes anything to a portal,
it learns that portal's schema, writes it down, and checks every planned write against it.

## Step 1: Discover the portal (read-only, free)

Use the HubSpot MCP's own tools. Nothing here writes.

1. `discover_hubspot_schema` with `GET_OBJECT_TYPES` and an empty filter: every object type,
   including custom objects, with the connected user's `readAccess` and `writeAccess`. Custom
   objects have portal-specific type names; never infer one from its label.
2. `search_properties` with no keywords, for each object the engine will touch: every
   property on it.
3. `get_properties` for the properties the engine will read or write: type and enumeration
   options. Fetch in batches; property details can be large.

## Step 2: Write the portal map

Save it next to `instance-config.json` and name it in `{HUBSPOT_PORTAL_MAP_FILE}`. The shape,
with a synthetic example in `examples/hubspot/portal-map.example.json`:

| Key | Meaning |
|---|---|
| `captured_on` | When discovery ran. Re-run discovery when the portal changes |
| `objects.<type>.write_access` | From discovery. False blocks every write to that object |
| `objects.<type>.dedupe_key` | The property that identifies a record (`email` for contacts, `domain` for companies). A create without it is blocked |
| `objects.<type>.required` | Properties a create must carry |
| `objects.<type>.append_only` | True for activity records such as notes, which are always new rows |
| `properties.<name>.type` | `string`, `number`, `bool`, `date`, `datetime` or `enumeration` |
| `properties.<name>.options` | For an enumeration, the allowed values (internal values, not labels) |
| `properties.<name>.multiple` | True for a multi-select; values are separated by `;` |
| `properties.<name>.owner` | `engine` or `human`, required on every property. **A human-managed property is never changed on an existing record**; a create may set it, since that is the record's first value |
| `properties.<name>.max_length` | Optional, when the portal enforces one |

**The `owner` column is the operator's decision, not discovery's.** Discovery says a property
exists; only the person who runs the portal knows whether a human maintains it. Mark every
property the engine does not create as `human` unless the operator says otherwise.

### Standard vs custom properties

Use HubSpot's standard properties where one fits (`email`, `domain`, `jobtitle`,
`lifecyclestage`); they are usually human-managed. The engine's own fields (opener, blueprint,
play, play-assigned-on, scores) are custom properties the operator creates in the portal, one
per engine field, named with `{INSTANCE_FIELD_PREFIX}` so they are recognizable. Creating them
is a UI step or a separate, approved action; this adapter does not create properties.

## Step 3: Check every planned write

Build the planned writes in the shape `manage_crm_objects` takes, then:

```bash
python3 scripts/hubspot_presync.py <portal map> planned-writes.json
```

It checks, without calling anything: the map itself is well-formed (every property has a
type and an owner); the object is writable; every property exists; no human-managed
property is changed on an existing record; values are strings; each value fits its type and options;
a create carries its dedupe key and required properties; association targets exist. Batches
over `manage_crm_objects`' limit of 10 objects are flagged to split. Exit 1 blocks the sync.

## Step 4: Write, then read back

`manage_crm_objects` requires showing the user a table of proposed changes and getting
approval before every create or update. That is HubSpot's own confirmation, and it stays in
place. After the write, read each property back and compare the value. Success and an empty
error are both compatible with having stored nothing (CLAUDE.md).

## What is still generic

No deployment has run the full motion on HubSpot, so its failure modes here are undocumented
and it stays in the Generic tier until one has. Report anything surprising: it is exactly
what moves a platform to Native.
