"""Сбор статистики генерации."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass, field


@dataclass
class Stats:
    posts_total: int = 0
    posts_public: int = 0
    posts_private: int = 0
    posts_friends: int = 0
    posts_custom: int = 0

    pages_index: int = 0
    pages_post: int = 0
    pages_tag: int = 0
    pages_static: int = 0   # tags.html, profile.html

    tags: Counter = field(default_factory=Counter)
    moods: Counter = field(default_factory=Counter)
    mood_icons: Counter = field(default_factory=Counter)
    music: Counter = field(default_factory=Counter)
    locations: Counter = field(default_factory=Counter)
    years: Counter = field(default_factory=Counter)

    def report(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("СТАТИСТИКА ГЕНЕРАЦИИ")
        lines.append("=" * 60)
        lines.append(f"Постов всего:          {self.posts_total}")
        lines.append(f"  public:              {self.posts_public}")
        lines.append(f"  private:             {self.posts_private}")
        lines.append(f"  friends:             {self.posts_friends}")
        lines.append(f"  custom:              {self.posts_custom}")
        lines.append("")
        lines.append("Сгенерировано файлов:")
        lines.append(f"  index-*.html:        {self.pages_index}")
        lines.append(f"  <post>.html:         {self.pages_post}")
        lines.append(f"  tag/*.html:          {self.pages_tag}")
        lines.append(f"  tags.html, profile:  {self.pages_static}")
        lines.append("")
        lines.append(f"Уникальных тегов:      {len(self.tags)}")
        lines.append("")
        lines.append("Mood icons (используются сейчас):")
        for name, cnt in sorted(self.mood_icons.items()):
            lines.append(f"  {name:<20} {cnt}")
        lines.append("")
        lines.append("Топ-10 тегов:")
        for name, cnt in self.tags.most_common(10):
            lines.append(f"  {name:<30} {cnt}")
        lines.append("")
        lines.append("Посты по годам:")
        for y in sorted(self.years):
            lines.append(f"  {y}: {self.years[y]}")
        return "\n".join(lines)