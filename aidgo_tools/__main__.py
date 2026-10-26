"""Command line entry point:  python -m aidgo_tools <command> [args]

  build       data/*.csv -> output/aidgo_kg.ttl, output/aidgo_kg_star.ttl, output/aidgo_kg.nt
  validate    SHACL + referential integrity on the built KG
  query       run queries/*.rq (all, or the ones named) -> output/cq_results/
  distance    semantic distance scores (all pairs, or: distance <legalId> <techId>)
  agreement   ISO/IEC 5259-3 extraction agreement with the second coding
  site        regenerate the data-driven parts of index.html and the KG explorer (--check: verify only)
  all         build, validate, query, distance, agreement, site
"""

import sys


def main() -> int:
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "build":
        from .build import main as m
        m()
        return 0
    if cmd == "validate":
        from .validate import main as m
        return m()
    if cmd == "query":
        from .query import main as m
        return m(rest)
    if cmd == "distance":
        from .distance import main as m
        return m(rest)
    if cmd == "agreement":
        from .agreement import main as m
        return m()
    if cmd == "site":
        from .site import main as m
        return m(rest)
    if cmd == "all":
        from . import agreement, build, distance, query, site, validate
        print("[1/6] build");     build.main()
        print("[2/6] validate")
        if validate.main():
            return 1
        print("[3/6] query");     query.main([])
        print("[4/6] distance");  distance.main([])
        print("[5/6] agreement"); agreement.main()
        print("[6/6] site");      return site.main([])
    print(f"unknown command: {cmd}\n{__doc__}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
