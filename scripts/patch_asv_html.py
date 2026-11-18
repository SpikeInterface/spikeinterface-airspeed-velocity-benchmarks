"""Patch asv's web UI templates for this project.

- graphdisplay.js, x-axis ticks in "commits" mode: one tick per benchmarked commit, "0.105.4" or "main (e9a02f30)"
- graphdisplay.js, hover tooltip: "2.1s @ 0.105.4 (a062c74e)" / "2.1s @ main (e9a02f30)" instead of "2.1s @ a062c74e"
- summarygrid.js: benchmark grid groups in GROUP_ORDER instead of alphabetical

By default it patches the templates inside the installed asv package, because `asv gh-pages` re-runs
`asv publish`, which recopies the templates and would undo a patch to the generated html/. Pass a built
site directory to patch it instead (e.g. a downloaded preview):

    python scripts/patch_asv_html.py            # installed asv (CI, before asv publish)
    python scripts/patch_asv_html.py asv-html
"""

import sys
from pathlib import Path

# benchmark grid: module groups in this order; groups not listed follow, in asv's alphabetical order
GROUP_ORDER = ["bench_imports", "bench_zarr", "bench_preprocessing", "bench_postprocessing", "bench_sortingcomponents"]

# {file: [(asv original, replacement)]}; each original must appear exactly once
PATCHES = {"graphdisplay.js": [
    (
        'options.xaxis.tickFormatter = function (v, axis) { return ""; };',
        # shortcut: one tick per benchmarked commit; labels will crowd once main has many monthly points
        """options.xaxis.axisLabel = 'version';
                options.xaxis.tickFormatter = null;
                var rev_to_tag = {};
                $.each($.asv.main_json.tags, function(tag, rev) { rev_to_tag[rev] = tag; });
                var revs = [];
                $.each(graphs, function(i, graph) {
                    $.each(graph.data, function(j, point) {
                        if (revs.indexOf(point[0]) === -1) revs.push(point[0]);
                    });
                });
                options.xaxis.ticks = $.map(revs, function(rev) {
                    var hash = $.asv.main_json.revision_to_hash[rev] || '';
                    return [[rev, rev_to_tag[rev] || "main (" + hash.slice(0, 8) + ")"]];
                });""",
    ),
    (
        '$.asv.pretty_unit(y, unit) + " @ " + commit_hash);',
        """$.asv.pretty_unit(y, unit) + " @ " + (function () {
                                // same x -> revision mapping as get_commit_hash()
                                var rev = date_scale ? date_to_revision[item.datapoint[0]] : item.datapoint[0];
                                var tag = null;
                                $.each($.asv.main_json.tags, function(t, r) { if (r == rev) tag = t; });
                                // untagged = main: asv.conf.json only tracks the main branch
                                return (tag || "main") + " (" + commit_hash + ")";
                            })());""",
    ),
], "summarygrid.js": [
    (
        """            groups[group].push(bm_name);
        });
        return groups;""",
        f"""            groups[group].push(bm_name);
        }});
        var order = {GROUP_ORDER!r};
        var ordered = {{}};
        $.each(order, function(i, g) {{ if (groups[g] !== undefined) ordered[g] = groups[g]; }});
        $.each(groups, function(g, bms) {{ if (ordered[g] === undefined) ordered[g] = bms; }});
        return ordered;""",
    ),
]}


def main():
    if len(sys.argv) > 1:
        www = Path(sys.argv[1])
    else:
        import asv

        www = Path(asv.__file__).parent / "www"
    for name, patches in PATCHES.items():
        path = www / name
        src = path.read_text()
        for original, replacement in patches:
            if replacement in src:
                continue
            if src.count(original) != 1:
                raise SystemExit(f"{path}: expected {original!r} exactly once; asv changed, update this script")
            src = src.replace(original, replacement)
        path.write_text(src)
        print(f"{path}: patched")


if __name__ == "__main__":
    main()
