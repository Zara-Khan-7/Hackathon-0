# Optimize Prompts

Run the self-improving optimization loop to enhance agent performance.

## When to use
Periodically (every 100 tasks) or on-demand to analyze agent performance and generate recommendations.

## Steps
1. Query OutcomeTracker for recent task outcomes
2. Run PromptOptimizer.analyze() to identify patterns
3. Check for low success rates by agent type
4. Check for recurring failure patterns
5. Check for slow-performing agents
6. Generate optimization recommendations
7. Log recommendations to audit trail
8. Apply approved optimizations

## Rules
- Minimum 10 samples required before generating recommendations
- Optimizations are logged but applied only with context
- Focus on actionable improvements: agent reassignment, prompt adjustment, error handling
- Never modify agent behavior without audit trail
