"""배치 러너 — Flask 앱과 분리된 단독 프로세스 (§11: 워커 중복 실행 방지).

사용:
  python -m batch.runner --once <job>    # 단발 실행 (개발/cron)
  python -m batch.runner --daemon        # APScheduler 상주 (프로덕션 systemd 1개)

잡: fetch_news(매시), daily_briefing(06:00), hot_posts(10분), close_poll(00:00)
"""
import argparse
import sys

from app.db.engine import create_db_engine
from config import Config


def make_engine():
    return create_db_engine(Config.DATABASE_URL)


def run_once(job_name, engine=None):
    engine = engine or make_engine()
    if job_name == "hot_posts":
        from batch.jobs import hot_posts
        return hot_posts.run(engine)
    if job_name == "close_poll":
        from batch.jobs import close_poll
        return close_poll.run(engine)
    if job_name == "fetch_news":
        from batch.jobs import fetch_news
        return fetch_news.run(engine)
    if job_name == "daily_briefing":
        from batch.jobs import daily_briefing
        return daily_briefing.run(engine)
    raise SystemExit(f"알 수 없는 잡: {job_name}")


def run_daemon():
    from apscheduler.schedulers.blocking import BlockingScheduler
    engine = make_engine()
    sched = BlockingScheduler(timezone="Asia/Seoul")
    sched.add_job(lambda: run_once("fetch_news", engine), "cron", minute=0)
    sched.add_job(lambda: run_once("daily_briefing", engine), "cron", hour=6, minute=0)
    sched.add_job(lambda: run_once("hot_posts", engine), "interval", minutes=10)
    sched.add_job(lambda: run_once("close_poll", engine), "cron", hour=0, minute=0)
    print("배치 데몬 시작 (Ctrl+C로 종료)")
    sched.start()


def main(argv=None):
    parser = argparse.ArgumentParser(description="오재 배치 러너")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--once", metavar="JOB",
                       choices=["fetch_news", "daily_briefing", "hot_posts", "close_poll"])
    group.add_argument("--daemon", action="store_true")
    args = parser.parse_args(argv)
    if args.once:
        result = run_once(args.once)
        print(f"[{args.once}] 완료: {result}")
    else:
        run_daemon()


if __name__ == "__main__":
    main(sys.argv[1:])
