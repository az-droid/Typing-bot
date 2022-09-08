from workers_kv.ext import async_workers_kv
from utils import envs

guild_ranking_namespace = async_workers_kv.Namespace(account_id=envs.WORKERS_KV_ACCOUNT,
                                                     namespace_id="b221db35965344b1b0e0a3d2c53cf6b4",
                                                     api_key=envs.CF_API_KEY)
global_ranking_namespace = async_workers_kv.Namespace(account_id=envs.WORKERS_KV_ACCOUNT,
                                                      namespace_id="41f52d54a13c453f8175d44b6083b74e",
                                                      api_key=envs.CF_API_KEY)
