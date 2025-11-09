# llm_providers/openrouter_handler.py

import requests
import json
from .llm_exception import LLMConnectionError

class OpenRouterHandler:
    def __init__(self, api_key=None, base_url=None, model=None, verify_on_init=False):
        if not api_key:
            raise ValueError("API key is required for OpenRouter")

        self.api_key = api_key
        # Respect provided base_url or fall back to the known API host
        self.base_url = base_url or "https://openrouter.ai/api/v1"
        # Use default model if none specified
        self.model = model or "mistralai/mistral-7b-instruct:free"
        self.provider = "openrouter"  # Add provider attribute for compatibility
        self.response_callback = None  # Initialize response callback
        
        # Set up headers according to OpenRouter API requirements
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/mnperrone/puentellm-mcp",  # Required by OpenRouter
            "X-Title": "PuenteLLM MCP",  # Application name
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "PuenteLLM/1.0.0"
        }
        
        print(f"Initializing OpenRouter handler with API URL: {self.base_url}")
        print(f"Model selected: {self.model}")
        
        # Configure session with SSL settings
        self.session = requests.Session()
        
        # Configure retries with backoff
        retry_strategy = requests.packages.urllib3.util.retry.Retry(
            total=3,
            backoff_factor=0.5,
            allowed_methods=["GET", "POST"],
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = requests.adapters.HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=1,
            pool_maxsize=1
        )
        self.session.mount("https://", adapter)
        
        print(f"Initializing OpenRouter handler with URL: {self.base_url}")
        print(f"Model: {self.model}")
        
        # Optionally verify connection during init. Default is to skip
        # verification to avoid hard failures on transient DNS/network issues.
        if verify_on_init:
            self._verify_connection()
            
    def set_response_callback(self, callback):
        """Set a callback function to handle streaming responses.
        
        Args:
            callback: A function that will be called with each chunk of the response.
        """
        self.response_callback = callback
        
    def set_mcp_handler(self, mcp_handler):
        """Set the MCP handler instance for this LLM handler.
        
        Args:
            mcp_handler: The MCP handler instance to use for processing MCP commands.
        """
        self.mcp_handler = mcp_handler
        print(f"MCP handler set for OpenRouter: {mcp_handler.__class__.__name__}")
        
    def generate_response(self, message, **kwargs):
        """Generate a response to the given message using the OpenRouter API.
        
        Args:
            message: The user's message to respond to.
            **kwargs: Additional arguments for the API call.
            
        Returns:
            The generated response text.
        """
        endpoint = f"{self.base_url}/chat/completions"
        
        messages = [
            {"role": "user", "content": message}
        ]
        
        data = {
            "model": self.model,
            "messages": messages,
            "stream": self.response_callback is not None,  # Enable streaming if callback is set
            **kwargs
        }
        
        try:
            if self.response_callback:
                # Handle streaming response
                with self.session.post(
                    endpoint,
                    headers=self.headers,
                    json=data,
                    stream=True
                ) as response:
                    if response.status_code != 200:
                        error_msg = f"Error en la respuesta de OpenRouter: {response.status_code} - {response.text}"
                        self.response_callback(error_msg, error=True)
                        return error_msg
                        
                    full_response = ""
                    for line in response.iter_lines():
                        if line:
                            chunk = json.loads(line)
                            if 'choices' in chunk and chunk['choices']:
                                delta = chunk['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    content = delta['content']
                                    full_response += content
                                    self.response_callback(content)
                    
                    return full_response
            else:
                # Handle non-streaming response
                response = self.session.post(
                    endpoint,
                    headers=self.headers,
                    json=data
                )
                
                if response.status_code != 200:
                    error_msg = f"Error en la respuesta de OpenRouter: {response.status_code} - {response.text}"
                    if self.response_callback:
                        self.response_callback(error_msg, error=True)
                    return error_msg
                
                result = response.json()
                if 'choices' in result and result['choices']:
                    return result['choices'][0]['message']['content']
                else:
                    error_msg = "No se pudo obtener una respuesta válida del modelo."
                    if self.response_callback:
                        self.response_callback(error_msg, error=True)
                    return error_msg
                    
        except Exception as e:
            error_msg = f"Error al generar la respuesta: {str(e)}"
            if self.response_callback:
                self.response_callback(error_msg, error=True)
            return error_msg

    def _verify_connection(self):
        """Verifica la conexión con OpenRouter y valida el API key"""
        try:
            print("\n=== Verifying OpenRouter Connection ===")
            print(f"Base URL: {self.base_url}")
            print(f"Selected model: {self.model}")
            
            # Intentar una petición simple al endpoint principal
            endpoint = f"{self.base_url}/chat/completions"
            print(f"Testing API connection to: {endpoint}")
            
            test_data = {
                "model": self.model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1
            }
            
            response = self.session.post(
                endpoint,
                headers=self.headers,
                json=test_data,
                timeout=10
            )
            
            print(f"Response status: {response.status_code}")
            
            # Check response status
            if response.status_code == 200:
                print("OpenRouter connection verified successfully")
                return True
            elif response.status_code == 401:
                raise LLMConnectionError("API key inválida o expirada")
            elif response.status_code == 403:
                raise LLMConnectionError("Acceso denegado. Verifica tu API key y permisos")
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', f"Error code: {response.status_code}")
                except:
                    error_msg = f"API returned status code {response.status_code}"
                
                print(f"Connection test failed: {error_msg}")
                print(f"Response content: {response.text}")
                raise LLMConnectionError(f"Error de conexión: {error_msg}")
                
        except requests.exceptions.SSLError as e:
            print(f"SSL Error: {str(e)}")
            raise LLMConnectionError("Error de SSL al conectar con OpenRouter. Verifica tu configuración de red.")
            
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {str(e)}")
            raise LLMConnectionError(f"Error de conexión con OpenRouter: {str(e)}")
            
        except Exception as e:
            print(f"OpenRouter connection failed: {str(e)}")
            raise LLMConnectionError(f"No se pudo conectar a OpenRouter: {str(e)}")
    
    def _make_request(self, endpoint, method="GET", data=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        print(f"Making request to {url}")
        
        # Configuración de timeouts y reintentos
        session = requests.Session()
        session.mount('https://', requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=1,
            pool_maxsize=1
        ))
        
        try:
            # Intentar resolver el dominio primero
            import socket
            try:
                socket.gethostbyname('openrouter.ai')
            except socket.gaierror:
                raise LLMConnectionError(
                    "No se puede resolver el dominio de OpenRouter. "
                    "Esto puede deberse a problemas de DNS o conexión a Internet. "
                    "Por favor, verifica tu conexión."
                )
            
            # Hacer la petición con timeouts explícitos
            if method.upper() == "GET":
                response = session.get(url, headers=self.headers, timeout=10)
            else:
                response = session.post(url, headers=self.headers, json=data, timeout=10)
            
            response.raise_for_status()
            result = response.json()
            print(f"Request successful: {endpoint}")
            return result
            
        except requests.exceptions.Timeout:
            error_msg = "La conexión con OpenRouter ha excedido el tiempo de espera"
            print(f"Request timeout: {error_msg}")
            raise LLMConnectionError(error_msg)
            
        except requests.exceptions.SSLError:
            error_msg = "Error de SSL al conectar con OpenRouter"
            print(f"SSL Error: {error_msg}")
            raise LLMConnectionError(error_msg)
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            try:
                if hasattr(e.response, 'json'):
                    error_details = e.response.json().get('error', {})
                    error_msg = error_details.get('message', error_msg)
            except:
                pass
            print(f"Request failed: {error_msg}")
            raise LLMConnectionError(f"OpenRouter API error: {error_msg}")

    def generate(self, prompt):
        """Generate a completion for the given prompt."""
        try:
            print("\n=== Generating OpenRouter Response ===")
            print(f"Using model: {self.model}")
            print(f"Prompt length: {len(prompt)}")
            
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            endpoint = f"{self.base_url}/chat/completions"
            print(f"Making request to: {endpoint}")
            
            response = self.session.post(
                endpoint,
                headers=self.headers,
                json=data,
                timeout=30
            ).json()
            
            if 'choices' in response and len(response['choices']) > 0:
                content = response['choices'][0]['message']['content']
                # Sanitize output for common tokenization artifacts
                content = self._sanitize_text(content)
                print(f"Successfully generated response of length: {len(content)}")
                return content
            else:
                raise LLMConnectionError("Response from OpenRouter did not contain expected content")
                
        except Exception as e:
            print(f"Generation error: {str(e)}")
            raise LLMConnectionError(f"Error generating response: {str(e)}")

    def stream(self, messages):
        """Stream a chat completion for the given messages."""
        try:
            # Check for placeholder API keys before making the request
            placeholder_keys = [
                "your_actual_openrouter_api_key_here",
                "sk-or-v1-your_actual_openrouter_api_key_here", 
                "test_key",
                "test_openrouter_key",
                "placeholder",
                "placeholder_key_required"  # Agregado para manejo de inicialización
            ]
            if (self.api_key in placeholder_keys or 
                "placeholder" in self.api_key.lower() or 
                "your_" in self.api_key.lower()):
                raise LLMConnectionError(
                    f"Configuración requerida: Necesitas una API key válida de OpenRouter. "
                    f"Ve a https://openrouter.ai/keys para obtener una, y configúrala en el "
                    f"menú 'Configurar LLM Remoto' o editando app_config.json."
                )
            
            print("\n=== Starting OpenRouter Stream ===")
            print(f"Using model: {self.model}")
            print(f"Number of messages: {len(messages)}")
            print(f"API Key (masked): {self.api_key[:10]}...{self.api_key[-4:] if len(self.api_key) > 14 else 'SHORT_KEY'}")
            
            data = {
                "model": self.model,
                "messages": messages,
                "stream": True,
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            headers = self.headers.copy()
            headers["Accept"] = "text/event-stream"
            print(f"Headers: {dict((k, v[:20]+'...' if k == 'Authorization' else v) for k, v in headers.items())}")
            
            endpoint = f"{self.base_url}/chat/completions"
            print(f"Streaming from URL: {endpoint}")
            
            # Implement an explicit retry loop for 429 (rate limit) that respects
            # the Retry-After header when present and uses exponential backoff with jitter.
            import time, random
            max_attempts = 4
            attempt = 0
            response = None
            while attempt < max_attempts:
                try:
                    response = self.session.post(
                        endpoint,
                        headers=headers,
                        json=data,
                        stream=True,
                        timeout=30
                    )
                except requests.exceptions.RequestException as e:
                    # Let the outer exception handler deal with non-HTTP errors
                    raise

                # If we hit a rate limit, try to wait and retry (respect Retry-After if present)
                if getattr(response, 'status_code', None) == 429:
                    attempt += 1
                    ra = response.headers.get('Retry-After') if hasattr(response, 'headers') else None
                    try:
                        # Retry-After may be seconds or HTTP-date; try int seconds first
                        wait = int(ra) if ra and ra.isdigit() else None
                    except Exception:
                        wait = None

                    if wait is None:
                        # Exponential backoff with jitter: base 1s,2s,4s
                        wait = (2 ** attempt) + random.uniform(0, 1)

                    print(f"OpenRouter returned 429 — attempt {attempt}/{max_attempts}, waiting {wait:.1f}s before retrying")
                    time.sleep(wait)
                    # Close response to free connection pool before retrying
                    try:
                        response.close()
                    except Exception:
                        pass
                    continue
                # Otherwise break and continue normal processing
                break
            
            print(f"Stream response status: {response.status_code}")
            if response.status_code == 404:
                print(f"Response content: {response.text}")
            response.raise_for_status()
            
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    # Decode the line first
                    decoded_line = line.decode('utf-8').strip()
                    
                    # Skip OpenRouter processing messages
                    if decoded_line.startswith(': OPENROUTER'):
                        continue
                        
                    # Handle SSE format
                    if decoded_line.startswith('data: '):
                        json_str = decoded_line[6:]
                    else:
                        json_str = decoded_line
                        
                    if json_str.strip() == "[DONE]":
                        break
                        
                    # Only try to parse if it looks like JSON
                    if json_str.startswith('{'):
                        chunk = json.loads(json_str)
                        if 'choices' in chunk and chunk['choices']:
                            delta = chunk['choices'][0].get('delta', {})
                            if 'content' in delta:
                                # Sanitize incremental content but preserve leading space so
                                # token boundaries are not lost when chunks are appended.
                                sanitized = self._sanitize_text(delta['content'], preserve_leading_space=True)
                                yield {"message": {"content": sanitized}}
                except json.JSONDecodeError as e:
                    if not decoded_line.startswith(': OPENROUTER'):
                        print(f"JSON decode error in stream: {e} -- line: {decoded_line}")
                    continue
                except Exception as e:
                    print(f"Error processing stream line: {e}")
                    continue
                                
        except requests.exceptions.RequestException as e:
            # Provide a clearer message for rate limiting (429) vs other network errors
            error_msg = str(e)
            try:
                resp = getattr(e, 'response', None)
                if resp is not None:
                    status_code = getattr(resp, 'status_code', None)
                    if status_code == 401:
                        # Special handling for 401 Unauthorized
                        try:
                            error_details = resp.json()
                            detailed_msg = error_details.get('error', {}).get('message', '') if isinstance(error_details, dict) else ''
                        except Exception:
                            detailed_msg = resp.text if hasattr(resp, 'text') else ''
                        
                        print(f"API Key being used: {self.api_key[:10]}...{self.api_key[-4:] if len(self.api_key) > 14 else 'SHORT_KEY'}")
                        print(f"Response details: {detailed_msg}")
                        
                        if "cookie" in detailed_msg.lower():
                            raise LLMConnectionError(
                                f"Error de autenticación (401): La API key parece ser inválida o incorrecta. "
                                f"Detalles: {detailed_msg}. Verifica que hayas configurado una API key válida de OpenRouter."
                            )
                        else:
                            raise LLMConnectionError(
                                f"Error de autenticación (401): API key inválida o expirada. "
                                f"Detalles: {detailed_msg}. Verifica tu API key de OpenRouter."
                            )
                    elif status_code == 429:
                        raise LLMConnectionError(
                            "OpenRouter rate limit (HTTP 429). Espera unos segundos o revisa tu cuota/API key."
                        )
                    # Try to extract JSON error if present
                    try:
                        error_details = resp.json()
                        if isinstance(error_details, dict) and 'error' in error_details:
                            error_msg = f"{error_msg} - {error_details['error'].get('message', '')}"
                    except Exception:
                        pass
            except LLMConnectionError:
                raise
            except Exception:
                pass

            print(f"Stream error: {error_msg}")
            raise LLMConnectionError(f"Error streaming from OpenRouter API: {error_msg}")
        except Exception as e:
            print(f"Unexpected error in stream: {str(e)}")
            raise LLMConnectionError(f"Error inesperado durante el streaming: {str(e)}")

    def list_models(self):
        """Returns the list of available models from OpenRouter."""
        try:
            print("\n=== Fetching Available Models from OpenRouter ===")
            response = self._make_request("models")
            
            if not response:
                print("No response received from OpenRouter models endpoint")
                return [self.model]
                
            models = response.get('data', [])
            if not models:
                print("No models found in the response")
                return [self.model]
                
            print("\nAvailable models:")
            for model in models:
                print(f"\nModel ID: {model.get('id')}")
                print(f"Name: {model.get('name', 'N/A')}")
                print(f"Description: {model.get('description', 'N/A')}")
                print(f"Context Length: {model.get('context_length', 'N/A')}")
                print(f"Pricing: {model.get('pricing', 'N/A')}")
                
            return [model['id'] for model in models if 'id' in model]
        except Exception as e:
            print(f"\nError fetching models: {str(e)}")
            return [self.model]

    def get_available_models(self):
        """Alias for list_models to maintain compatibility with LLMMCPHandler."""
        return self.list_models()

    def _sanitize_text(self, text: str, preserve_leading_space: bool = False) -> str:
        """Lightweight sanitizer to remove tokenization markers commonly returned by some models.

        - Replaces the special subword joiner '▁' with spaces.
        - Removes angle-bracket style markers like `<...>` which sometimes appear as control tokens.
        - Collapses multiple spaces and trims edges.

        This sanitizer is intentionally conservative; it only performs harmless whitespace
        normalization and removes obvious control tokens. If you prefer to disable it,
        set the PUENTE_DISABLE_SANITIZER environment variable to '1'.
        """
        try:
            import os, re
            if os.environ.get('PUENTE_DISABLE_SANITIZER', '') == '1':
                return text

            # Replace subword marker with a space
            text = text.replace('▁', ' ')

            # Remove tokens enclosed in angle brackets (also handles fullwidth vertical bars)
            # e.g. '<｜begin▁of▁sentence｜>' or '<something>'
            text = re.sub(r'<[^>]*>', '', text)

            # Collapse multiple spaces
            text = re.sub(r'\s+', ' ', text)

            # Trim depending on context: for final content trim both ends, for
            # incremental streaming chunks preserve leading space (token boundary).
            if preserve_leading_space:
                text = text.rstrip()
            else:
                text = text.strip()

            # Optionally perform auto-spacing heuristics when enabled via env or app config
            enable_auto = False
            try:
                if os.environ.get('PUENTE_ENABLE_AUTO_SPACING', '') == '1':
                    enable_auto = True
                else:
                    # Try reading app config flag if available
                    from app_config import AppConfig
                    cfg = AppConfig()
                    if cfg.get('auto_space_model_output'):
                        enable_auto = True
            except Exception:
                # If config cannot be read, fall back to env var only
                pass

            if enable_auto:
                try:
                    # First, attempt conservative dictionary-based segmentation on long merged runs.
                    # Doing this early avoids smaller regex insertions from splitting inside
                    # longer tokens and producing fragmented words.
                    text = self._auto_space_text(text)

                    # 1) Ensure punctuation followed by letters has a space: ',word' -> ', word'
                    text = re.sub(r'([,;:\.\?!，。])(?=[^\s])', r"\1 ", text)

                    # 2) (Removed) Avoid aggressive insertion of spaces after short common words
                    # because it tends to split legitimate words that begin with those prefixes
                    # (e.g. 'consulta' -> 'con sulta'). We rely primarily on the conservative
                    # dictionary-based segmentation above to fix merged words.

                    # 3) Collapse multiple spaces again and trim
                    text = re.sub(r'\s+', ' ', text).strip()
                except Exception:
                    pass

            return text
        except Exception:
            return text

    def _auto_space_text(self, text: str) -> str:
        """Attempt to split merged words using a small Spanish word frequency dictionary.

        This uses dynamic programming (Viterbi-like) to segment contiguous letter runs
        without spaces into likely word sequences. It's intentionally conservative and
        acts only on sequences of letters longer than a threshold to avoid changing
        normal text.
        """
        try:
            import re

            # Simple Spanish frequency dictionary (common words) with heuristic scores.
            # This list is intentionally small — it focuses on high-frequency tokens useful
            # for fixing model concatenations in conversational output.
            freq = {
                'de': 10000, 'la': 9000, 'el': 9000, 'y': 8500, 'a': 8000, 'en': 8000,
                'un': 7900, 'una': 7000, 'que': 7500, 'para': 7200, 'con': 7100,
                'por': 6800, 'como': 6500, 'más': 6400, 'estoy': 6000, 'soy': 6000,
                'modelo': 4000, 'lenguaje': 3000, 'artificial': 3000, 'desarrollado': 2000,
                'por': 6800, 'estoy': 6000, 'aqui': 500, 'aquí': 500, 'para': 7200,
                'ayudarte': 1000, 'ayudar': 2000, 'consulta': 1500, 'consultas': 800,
                'problemas': 1200, 'consejos': 900, 'conocimientos': 900, 'generales': 800,
                'tengas': 700, 'hoy': 1000, 'puedo': 1100, 'en': 8000
            }

            # Precompute log-probs
            import math
            max_freq = max(freq.values())
            logp = {w: math.log(v / max_freq) for w, v in freq.items()}

            def best_split(s: str):
                n = len(s)
                # dp[i] = (score, split_point)
                dp = [(-1e9, -1)] * (n + 1)
                dp[0] = (0.0, -1)
                for i in range(n):
                    if dp[i][0] < -1e8:
                        continue
                    # try substrings up to reasonable length
                    for j in range(i + 1, min(n, i + 20) + 1):
                        w = s[i:j].lower()
                        if w in logp:
                            score = dp[i][0] + logp[w]
                            if score > dp[j][0]:
                                dp[j] = (score, i)
                # if we couldn't cover, return None
                if dp[n][0] < -1e8:
                    return None
                # reconstruct
                parts = []
                idx = n
                while idx > 0:
                    prev = dp[idx][1]
                    parts.append(s[prev:idx])
                    idx = prev
                return ' '.join(reversed(parts))

            # Replace long merged runs (letters and punctuation-free) with segmented versions
            def repl(match):
                token = match.group(0)
                if len(token) < 6:
                    return token
                seg = best_split(token)
                return seg if seg else token

            return re.sub(r"[A-Za-záéíóúñÁÉÍÓÚÑ]{6,}", repl, text)
        except Exception:
            return text
