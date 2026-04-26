#!/bin/bash
# phase5_migrate_blog_posts.sh
# Migrates table_Alpha_Blog_Posts into social_posts (platform='blog'), then drops the old table.
# Run as: bash $CHIEFOS_HOME/scripts/phase5_migrate_blog_posts.sh

DB="$CHIEFOS_HOME/chiefos.db"

echo "Backing up DB before migration..."
sqlite3 "$DB" ".dump" > $CHIEFOS_HOME/alpha_backup_phase5_$(date +%Y%m%d_%H%M).sql
echo "Backup saved."

echo "Migrating blog posts into social_posts..."
sqlite3 "$DB" <<'SQL'
INSERT INTO social_posts (id, title, platform, status, post_date)
SELECT
    'blog_' || printf('%03d', id),
    title,
    'blog',
    status,
    DATE(created_at)
FROM table_Alpha_Blog_Posts;
SQL

echo "Verifying migration..."
sqlite3 "$DB" "SELECT id, title, platform, status FROM social_posts WHERE platform='blog';"

echo "Dropping table_Alpha_Blog_Posts..."
sqlite3 "$DB" "DROP TABLE table_Alpha_Blog_Posts;"

echo "Verifying table is gone..."
sqlite3 "$DB" ".tables" | tr ' ' '\n' | grep -i blog || echo "table_Alpha_Blog_Posts confirmed dropped."

echo "Done."
