from environs import Env
# from git import Repo


env = Env()
env.read_env()

ALLOWED_HOSTS = env('ALLOWED_HOSTS', ['127.0.0.1', 'localhost', '0.0.0.0'])
print(ALLOWED_HOSTS)
