import cProfile
from differential_equation  import main as de_main
from TSP import main as tsp_main
from cryptography import main as crypt_main
def profile(fn, outname):
    profiler = cProfile.Profile()
    profiler.enable()
    fn()
    profiler.disable()
    profiler.dump_stats(outname)
    print(f"→ Profile for {fn.__name__} saved to {outname}")

if __name__ == '__main__':
    profile(de_main,  'de_profile.prof')
    profile(tsp_main, 'tsp_profile.prof')
    print("Done. Use `snakeviz de_profile.prof` or `snakeviz tsp_profile.prof` to inspect.")
