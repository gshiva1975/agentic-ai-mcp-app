# finance_service/service.py

from finance_service.config import settings


class FinanceService:

    def __init__(self, llm, store=None, embed=None, researcher_agent=None):
        self.mode = settings.EXPERIMENT_MODE
        self.llm  = llm

        if self.mode == "BASELINE":
            from finance_service.baseline_model import BaselineFinancialModel
            self.engine = BaselineFinancialModel(llm)

        elif self.mode == "OPTIMIZED":
            from finance_service.optimized_pipeline import OptimizedFinancePipeline

            if store is None or embed is None or researcher_agent is None:
                raise ValueError(
                    "OPTIMIZED mode requires store, embed, and researcher_agent."
                )
            self.engine = OptimizedFinancePipeline(
                llm=llm,
                store=store,
                embed=embed,
                researcher_agent=researcher_agent,
            )

        else:
            raise ValueError(f"Unsupported EXPERIMENT_MODE: {self.mode}")

    def analyze(self, query: str):
        return self.engine.analyze(query)
