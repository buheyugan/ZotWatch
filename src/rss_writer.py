from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

from .models import RankedWork

logger = logging.getLogger(__name__)


def write_rss(
    works: Iterable[RankedWork],
    output_path: Path | str,
    *,
    title: str = "ZotWatcher Feed",
    link: str = "https://example.com",
    description: str = "AI assisted literature watch",
) -> Path:
    works_list = list(works)
    
    # 1. 在根节点引入 dc 和 prism 命名空间
    rss = ET.Element("rss", version="2.0", attrib={
        "xmlns:dc": "http://purl.org/dc/elements/1.1/",
        "xmlns:prism": "http://prismstandard.org/namespaces/basic/2.0/"
    })
    
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = title
    ET.SubElement(channel, "link").text = link
    ET.SubElement(channel, "description").text = description
    ET.SubElement(channel, "lastBuildDate").text = _format_rfc822(datetime.now(timezone.utc))

    for work in works_list:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = work.title
        if work.url:
            ET.SubElement(item, "link").text = work.url
        ET.SubElement(item, "guid").text = work.identifier
        ET.SubElement(item, "pubDate").text = _format_rfc822(work.published)
        
        # --- 新增 1：处理 bioRxiv 期刊名统一 ---
        venue_name = work.venue
        # 通过 source 字段或 DOI 判定是否为 bioRxiv 预印本
        if work.source.lower() == "biorxiv" or (work.doi and "10.1101/" in work.doi):
            venue_name = "bioRxiv"

        if venue_name:
            ET.SubElement(item, "category").text = venue_name
            ET.SubElement(item, "dc:source").text = venue_name
            ET.SubElement(item, "prism:publicationName").text = venue_name
            
        # --- 新增 2：提取并写入作者信息 ---
        if work.authors:
            for author in work.authors:
                # Zotero 会自动抓取 dc:creator 作为文献的 Creator/Author
                ET.SubElement(item, "dc:creator").text = author
                
        description_lines = []
        if work.abstract:
            description_lines.append(work.abstract)
        published_text = work.published.isoformat() if work.published else "Unknown"
        description_lines.append(f"Published: {published_text}")
        
        ET.SubElement(item, "description").text = "\n".join(description_lines)

    tree = ET.ElementTree(rss)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    logger.info("Wrote RSS feed with %d items to %s", len(works_list), path)
    return path

def _format_rfc822(dt: datetime | None) -> str:
    if dt is None:
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")


__all__ = ["write_rss"]
