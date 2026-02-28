/**
 * Load traces.json, shift timestamps to now, regenerate IDs, and upload via RunTree.
 */

import "dotenv/config";
import * as fs from "fs";
import { parseArgs } from "util";
import { Client, RunTree } from "langsmith";
import { randomUUID } from "crypto";

function parseDt(s: string | null): Date | null {
  if (s === null || s === undefined) {
    return null;
  }
  return new Date(s);
}

async function main() {
  const { values } = parseArgs({
    options: {
      project: { type: "string", default: "default" },
      input: { type: "string", default: "synthetic_traces.json" },
    },
    strict: false,
  });

  const projectName = values.project as string;
  const inputFile = values.input as string;

  const runs: any[] = JSON.parse(fs.readFileSync(inputFile, "utf-8"));
  console.log(`Loaded ${runs.length} runs from ${inputFile}`);

  // Calculate time shift so traces appear recent
  let latest = new Date(0);
  for (const r of runs) {
    if (r.start_time) {
      const dt = parseDt(r.start_time)!;
      if (dt > latest) latest = dt;
    }
  }
  const timeDeltaMs = Date.now() - latest.getTime();
  console.log(`Shifting timestamps by: ${timeDeltaMs}ms`);

  // Build ID map (new UUIDs for time-ordering)
  const idMap: Record<string, string> = {};
  for (const run of runs) {
    for (const field of ["id", "trace_id", "parent_run_id"]) {
      const oldId = run[field];
      if (oldId && !(oldId in idMap)) {
        idMap[oldId] = randomUUID();
      }
    }
  }

  // Group runs by trace and transform
  const traces: Record<string, any[]> = {};
  for (const run of runs) {
    const traceId = run.trace_id;
    if (!traces[traceId]) traces[traceId] = [];

    const startTime = parseDt(run.start_time);
    const endTime = run.end_time ? parseDt(run.end_time) : null;

    traces[traceId].push({
      id: idMap[run.id],
      parent_run_id: idMap[run.parent_run_id] || undefined,
      name: run.name,
      run_type: run.run_type,
      inputs: run.inputs,
      outputs: run.outputs || undefined,
      error: run.error || undefined,
      extra: run.extra || undefined,
      tags: run.tags || undefined,
      start_time: startTime
        ? new Date(startTime.getTime() + timeDeltaMs)
        : undefined,
      end_time: endTime
        ? new Date(endTime.getTime() + timeDeltaMs)
        : undefined,
    });
  }

  const client = new Client();
  const traceKeys = Object.keys(traces);
  console.log(
    `Uploading ${traceKeys.length} traces to project '${projectName}'...`
  );

  for (let i = 0; i < traceKeys.length; i++) {
    const traceRuns = traces[traceKeys[i]];

    // Sort by start_time, root first (no parent)
    traceRuns.sort((a: any, b: any) => {
      const aIsChild = a.parent_run_id != null ? 1 : 0;
      const bIsChild = b.parent_run_id != null ? 1 : 0;
      if (aIsChild !== bIsChild) return aIsChild - bIsChild;
      return (
        (a.start_time?.getTime() || 0) - (b.start_time?.getTime() || 0)
      );
    });

    const treeMap: Record<string, RunTree> = {};
    let rootTree: RunTree | null = null;

    for (const run of traceRuns) {
      if (run.parent_run_id == null) {
        // Root run
        rootTree = new RunTree({
          id: run.id,
          name: run.name,
          run_type: run.run_type,
          inputs: run.inputs,
          start_time: run.start_time,
          extra: run.extra,
          tags: run.tags,
          project_name: projectName,
          client,
        });
        treeMap[run.id] = rootTree;
      } else {
        // Child run
        const parent = treeMap[run.parent_run_id];
        if (parent) {
          const child = parent.createChild({
            name: run.name,
            run_type: run.run_type,
            id: run.id,
            inputs: run.inputs,
            start_time: run.start_time,
            extra: run.extra,
            tags: run.tags,
          });
          treeMap[run.id] = child;
        }
      }
    }

    // End all runs (children first)
    for (let j = traceRuns.length - 1; j >= 0; j--) {
      const run = traceRuns[j];
      const tree = treeMap[run.id];
      if (tree) {
        tree.end({
          outputs: run.outputs,
          error: run.error,
          endTime: run.end_time,
        });
      }
    }

    if (rootTree) {
      await rootTree.postRun();
    }

    if ((i + 1) % 10 === 0) {
      console.log(`  Uploaded ${i + 1}/${traceKeys.length} traces`);
    }
  }

  // Wait for all background operations to complete
  console.log("Flushing...");
  await client.flush();
  console.log("Done!");
}

main().catch(console.error);
