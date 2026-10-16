"""Deterministic one-hour interview curricula. Role selects domains; evidence selects depth."""
from __future__ import annotations

ROLE_PLANS = {
    'quant_research': [
        {'id':'hr','label':'HR & resume cross-examination','minutes':15},
        {'id':'math','label':'Probability, statistics, stochastic processes','minutes':20},
        {'id':'coding','label':'Python algorithms & quantitative coding','minutes':15},
        {'id':'quant','label':'Research design, backtesting & risk','minutes':10},
    ],
    'quant_developer': [
        {'id':'hr','label':'HR & resume cross-examination','minutes':15},
        {'id':'coding','label':'Algorithms, data structures, complexity','minutes':20},
        {'id':'systems','label':'Concurrency, latency & systems','minutes':15},
        {'id':'quant','label':'Quantitative domain fundamentals','minutes':10},
    ],
    'ml_engineer': [
        {'id':'hr','label':'HR & resume cross-examination','minutes':15},
        {'id':'coding','label':'Coding & debugging','minutes':15},
        {'id':'ml','label':'ML fundamentals and experiments','minutes':20},
        {'id':'systems','label':'Serving, MLOps & inference','minutes':10},
    ],
    'ai_researcher': [
        {'id':'hr','label':'HR & research resume cross-examination','minutes':15},
        {'id':'transformer','label':'Transformer mechanisms & trade-offs','minutes':15},
        {'id':'rl','label':'RL, alignment & modern generative models','minutes':15},
        {'id':'research','label':'Mathematical validity and research design','minutes':15},
    ],
    'agent_engineer': [
        {'id':'hr','label':'HR & resume cross-examination','minutes':15},
        {'id':'coding','label':'Algorithms and coding','minutes':15},
        {'id':'transformer','label':'LLM fundamentals','minutes':10},
        {'id':'agent','label':'Agent harness, MCP, memory and evaluation','minutes':20},
    ],
    'generative_researcher': [
        {'id':'hr','label':'HR & research resume cross-examination','minutes':15},
        {'id':'math','label':'Probability and optimization','minutes':10},
        {'id':'generation','label':'Diffusion, flow matching, VAE, DiT','minutes':25},
        {'id':'research','label':'Research design and reproducibility','minutes':10},
    ],
}
ROLE_LABELS = {
    'quant_research':'Quant Researcher / Trader',
    'quant_developer':'Quant Developer',
    'ml_engineer':'Machine Learning Engineer',
    'ai_researcher':'AI Research Scientist',
    'agent_engineer':'LLM / Agent Engineer',
    'generative_researcher':'Generative AI Researcher',
}

def choose_phase(role: str, active_seconds: float):
    if role not in ROLE_PLANS:
        raise ValueError('Unsupported interview role')
    cutoff = 0
    for phase in ROLE_PLANS[role]:
        cutoff += phase['minutes'] * 60
        if active_seconds < cutoff:
            return phase
    return ROLE_PLANS[role][-1]

def is_code(phase_id: str) -> bool:
    return phase_id == 'coding'
