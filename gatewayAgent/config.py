import os
from dataclasses import dataclass

def as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

@dataclass
class GatewayConfig:
    in_cse_base_url: str
    originator_id: str
    callback_url: str
    application_name: str
    subscription_name: str
    image: str
    acme_image:str
    host_cse_base_dir:str
    cnt_cse_base_dir:str
    docker_host:str
    gateway_host_addr: str
    log_level: str = "INFO"
    

    tls_enabled: bool = False
    tls_verify: bool = True
    tls_ca_cert: str | None = None
    tls_client_cert: str | None = None
    tls_client_key: str | None = None

    # max_mn: str|None=None

    @classmethod
    def from_env(cls) -> "GatewayConfig":
        cfg = cls(
            in_cse_base_url=os.environ["IN_CSE_BASE_URL"],
            originator_id=os.environ["ORIGINATOR_ID"],
            callback_url=os.environ["CALLBACK_URL"],
            application_name=os.environ["APPLICATION_NAME"],
            subscription_name=os.environ["SUBSCRIPTION_NAME"],
            image=os.environ["IMAGE"],
            acme_image=os.environ["ACME_IMAGE"],
            host_cse_base_dir=os.environ["HOST_CSE_BASE_DIR"],
            cnt_cse_base_dir=os.environ["CONTAINER_CSE_BASE_DIR"],
            docker_host=os.environ["DOCKER_HOST"],
            gateway_host_addr=os.environ["GATEWAY_HOST_ADDR"],
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            
            

            tls_enabled=as_bool(os.getenv("TLS_ENABLED"), False),
            tls_verify=as_bool(os.getenv("TLS_VERIFY"), True),
            tls_ca_cert=os.getenv("TLS_CA_CERT"),
            tls_client_cert=os.getenv("TLS_CLIENT_CERT"),
            tls_client_key=os.getenv("TLS_CLIENT_KEY"),

            # max_mn=int(os.getenv("MAX_MN", "2"))
        )
        cfg.validate()
        return cfg

    def validate(self):
        if not self.in_cse_base_url:
            raise ValueError("MN_CSE_BASE_URL is required")
        if not self.originator_id:
            raise ValueError("ORIGINATOR_ID is required")
        if not self.callback_url:
            raise ValueError("CALLBACK_URL is required")
        if not self.application_name:
            raise ValueError("APPLICATION_BASE_NAME is required")
        if not self.subscription_name:
            raise ValueError("SUBSCRIPTION_NAME is required")
        if not self.image:
            raise ValueError("IMAGE is required")
        if not self.acme_image:
            raise ValueError("ACME_IMAGE is required")
        if not self.host_cse_base_dir:
            raise ValueError("HOST_CSE_BASE_DIR is required")
        if not self.cnt_cse_base_dir:
            raise ValueError("CNT_CSE_BASE_DIR is required")
        if not self.docker_host:
            raise ValueError("DOCKER_HOST is required")
        if not self.gateway_host_addr:
            raise ValueError("GATEWAY_HOST_ADDR is required")

        if self.tls_enabled:
            if self.tls_verify and self.tls_ca_cert is None:
                raise ValueError("TLS_CA_CERT is required when TLS is enabled and verification is on")

            cert_given = bool(self.tls_client_cert)
            key_given = bool(self.tls_client_key)
            if cert_given != key_given:
                raise ValueError("TLS_CLIENT_CERT and TLS_CLIENT_KEY must be provided together")