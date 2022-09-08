from workers_kv.ext import async_workers_kv
from utils import envs

guild_ranking_namespace = async_workers_kv.Namespace(account_id=envs.WORKERS_KV_ACCOUNT,
                                                     namespace_idenvs.WORKERS_KV_NAMESPACE,
                                                     api_key=envs.CF_API_KEY)
global_ranking_namespace = async_workers_kv.Namespace(account_id=envs.WORKERS_KV_ACCOUNT,
                                                      namespace_id=envs.WORKERS_KV_NAMESPACE,
                                                      api_key=envs.CF_API_KEY)
