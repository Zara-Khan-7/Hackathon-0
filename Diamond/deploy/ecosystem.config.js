// PM2 Process Configuration — Platinum Tier
// Start all: pm2 start ecosystem.config.js
// Status: pm2 status
// Logs: pm2 logs

module.exports = {
  apps: [
    {
      name: "orchestrator",
      script: "python",
      args: "-m src.orchestrator.orchestrator --role cloud --dry-run",
      cwd: "/opt/ai-employee",
      restart_delay: 5000,
      max_restarts: 10,
      env: {
        DRY_RUN: "true",
        AGENT_ROLE: "cloud",
        AGENT_ID: "cloud-001",
        GIT_SYNC_ENABLED: "true",
      },
    },
    {
      name: "gmail-watcher",
      script: "python",
      args: "-m src.watchers.gmail_watcher",
      cwd: "/opt/ai-employee",
      restart_delay: 10000,
    },
    {
      name: "linkedin-watcher",
      script: "python",
      args: "-m src.watchers.linkedin_watcher",
      cwd: "/opt/ai-employee",
      restart_delay: 10000,
    },
    {
      name: "facebook-watcher",
      script: "python",
      args: "-m src.watchers.facebook_watcher",
      cwd: "/opt/ai-employee",
      restart_delay: 10000,
    },
    {
      name: "instagram-watcher",
      script: "python",
      args: "-m src.watchers.instagram_watcher",
      cwd: "/opt/ai-employee",
      restart_delay: 10000,
    },
    {
      name: "twitter-watcher",
      script: "python",
      args: "-m src.watchers.twitter_watcher",
      cwd: "/opt/ai-employee",
      restart_delay: 10000,
    },
    {
      name: "scheduler",
      script: "python",
      args: "-m src.scheduler.scheduler",
      cwd: "/opt/ai-employee",
      restart_delay: 5000,
    },
    {
      name: "health-monitor",
      script: "python",
      args: "-c \"from src.health.health_monitor import HealthMonitor; import time; m=HealthMonitor(); [time.sleep(60) or m.run_all_checks() for _ in iter(int,1)]\"",
      cwd: "/opt/ai-employee",
      restart_delay: 30000,
    },
  ],
};
