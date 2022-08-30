import pstats
p = pstats.Stats('performance.file')
p.sort_stats('tottime').print_stats()