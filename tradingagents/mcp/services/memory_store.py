"""
记忆存储服务模块
"""

import asyncio
import logging
import json
import sqlite3
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class MemoryStoreService:
    """记忆存储服务"""
    
    def __init__(self):
        self.db_path = os.getenv("MEMORY_DB_PATH", "./data/memory.db")
        self.cache = {}
        self.cache_timeout = 300  # 5分钟缓存
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """确保数据库存在并创建表"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建决策记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trading_decisions (
                        id TEXT PRIMARY KEY,
                        ticker TEXT NOT NULL,
                        decision TEXT NOT NULL,
                        context TEXT NOT NULL,
                        reasoning TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        outcome TEXT,
                        performance REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建相似案例索引表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS similarity_index (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        decision_id TEXT NOT NULL,
                        feature_type TEXT NOT NULL,
                        feature_value TEXT NOT NULL,
                        weight REAL DEFAULT 1.0,
                        FOREIGN KEY (decision_id) REFERENCES trading_decisions (id)
                    )
                ''')
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Memory store health check failed: {e}")
            return False
    
    async def store_decision(
        self,
        ticker: str,
        decision: str,
        context: Dict[str, Any],
        reasoning: str
    ) -> str:
        """存储交易决策"""
        try:
            decision_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 存储主决策记录
                cursor.execute('''
                    INSERT INTO trading_decisions 
                    (id, ticker, decision, context, reasoning, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    decision_id, ticker, decision, 
                    json.dumps(context), reasoning, timestamp
                ))
                
                # 创建特征索引用于相似性搜索
                await self._create_feature_index(cursor, decision_id, ticker, context)
                
                conn.commit()
            
            logger.info(f"Stored decision {decision_id} for {ticker}")
            return decision_id
            
        except Exception as e:
            logger.error(f"Failed to store decision: {e}")
            raise
    
    async def retrieve_similar_cases(
        self,
        context: Dict[str, Any],
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """检索相似案例"""
        try:
            cache_key = f"similar_{hash(str(context))}_{n_results}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取所有决策记录
                cursor.execute('''
                    SELECT id, ticker, decision, context, reasoning, 
                           timestamp, outcome, performance
                    FROM trading_decisions
                    ORDER BY created_at DESC
                    LIMIT 100
                ''')
                
                records = cursor.fetchall()
                
                # 计算相似度
                similar_cases = []
                for record in records:
                    try:
                        stored_context = json.loads(record[3])
                        similarity_score = self._calculate_similarity(context, stored_context)
                        
                        if similarity_score > 0.3:  # 相似度阈值
                            similar_cases.append({
                                "id": record[0],
                                "ticker": record[1],
                                "decision": record[2],
                                "context": stored_context,
                                "reasoning": record[4],
                                "timestamp": record[5],
                                "outcome": json.loads(record[6]) if record[6] else None,
                                "performance": record[7],
                                "similarity_score": similarity_score
                            })
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Failed to parse record {record[0]}: {e}")
                        continue
                
                # 按相似度排序
                similar_cases.sort(key=lambda x: x["similarity_score"], reverse=True)
                result = similar_cases[:n_results]
                
                # 缓存结果
                self._cache_data(cache_key, result)
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to retrieve similar cases: {e}")
            return []
    
    async def update_outcome(
        self,
        memory_id: str,
        outcome: Dict[str, Any]
    ) -> bool:
        """更新决策结果"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 计算性能指标
                performance = self._calculate_performance(outcome)
                
                cursor.execute('''
                    UPDATE trading_decisions 
                    SET outcome = ?, performance = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (json.dumps(outcome), performance, memory_id))
                
                if cursor.rowcount == 0:
                    logger.warning(f"No record found with id {memory_id}")
                    return False
                
                conn.commit()
                logger.info(f"Updated outcome for decision {memory_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update outcome: {e}")
            return False
    
    async def get_decision_history(
        self,
        ticker: Optional[str] = None,
        decision_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取决策历史"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT id, ticker, decision, context, reasoning, 
                           timestamp, outcome, performance
                    FROM trading_decisions
                    WHERE 1=1
                '''
                params = []
                
                if ticker:
                    query += " AND ticker = ?"
                    params.append(ticker)
                
                if decision_type:
                    query += " AND decision = ?"
                    params.append(decision_type)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                records = cursor.fetchall()
                
                history = []
                for record in records:
                    try:
                        history.append({
                            "id": record[0],
                            "ticker": record[1],
                            "decision": record[2],
                            "context": json.loads(record[3]),
                            "reasoning": record[4],
                            "timestamp": record[5],
                            "outcome": json.loads(record[6]) if record[6] else None,
                            "performance": record[7]
                        })
                    except json.JSONDecodeError:
                        continue
                
                return history
                
        except Exception as e:
            logger.error(f"Failed to get decision history: {e}")
            return []
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 总体统计
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_decisions,
                        COUNT(CASE WHEN outcome IS NOT NULL THEN 1 END) as completed_decisions,
                        AVG(CASE WHEN performance IS NOT NULL THEN performance END) as avg_performance,
                        MAX(performance) as best_performance,
                        MIN(performance) as worst_performance
                    FROM trading_decisions
                ''')
                
                stats = cursor.fetchone()
                
                # 按决策类型统计
                cursor.execute('''
                    SELECT decision, COUNT(*), AVG(performance)
                    FROM trading_decisions
                    WHERE performance IS NOT NULL
                    GROUP BY decision
                ''')
                
                decision_stats = cursor.fetchall()
                
                return {
                    "total_decisions": stats[0],
                    "completed_decisions": stats[1],
                    "avg_performance": stats[2] or 0,
                    "best_performance": stats[3] or 0,
                    "worst_performance": stats[4] or 0,
                    "decision_breakdown": [
                        {
                            "decision_type": row[0],
                            "count": row[1],
                            "avg_performance": row[2] or 0
                        }
                        for row in decision_stats
                    ],
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {"error": str(e)}
    
    async def _create_feature_index(
        self, 
        cursor, 
        decision_id: str, 
        ticker: str, 
        context: Dict[str, Any]
    ):
        """创建特征索引"""
        try:
            # 股票代码特征
            cursor.execute('''
                INSERT INTO similarity_index (decision_id, feature_type, feature_value, weight)
                VALUES (?, ?, ?, ?)
            ''', (decision_id, "ticker", ticker, 1.0))
            
            # 提取关键特征
            for key, value in context.items():
                if isinstance(value, (str, int, float)):
                    cursor.execute('''
                        INSERT INTO similarity_index (decision_id, feature_type, feature_value, weight)
                        VALUES (?, ?, ?, ?)
                    ''', (decision_id, f"context_{key}", str(value), 0.5))
                    
        except Exception as e:
            logger.warning(f"Failed to create feature index: {e}")
    
    def _calculate_similarity(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> float:
        """计算上下文相似度"""
        try:
            # 简单的相似度计算
            common_keys = set(context1.keys()) & set(context2.keys())
            if not common_keys:
                return 0.0
            
            similarity_scores = []
            
            for key in common_keys:
                val1, val2 = context1[key], context2[key]
                
                if isinstance(val1, str) and isinstance(val2, str):
                    # 字符串相似度
                    if val1.lower() == val2.lower():
                        similarity_scores.append(1.0)
                    else:
                        similarity_scores.append(0.0)
                        
                elif isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    # 数值相似度（归一化差异）
                    if val1 == 0 and val2 == 0:
                        similarity_scores.append(1.0)
                    elif val1 == 0 or val2 == 0:
                        similarity_scores.append(0.0)
                    else:
                        diff = abs(val1 - val2) / max(abs(val1), abs(val2))
                        similarity_scores.append(max(0, 1 - diff))
                else:
                    # 其他类型，直接比较
                    similarity_scores.append(1.0 if val1 == val2 else 0.0)
            
            return sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
            
        except Exception as e:
            logger.warning(f"Failed to calculate similarity: {e}")
            return 0.0
    
    def _calculate_performance(self, outcome: Dict[str, Any]) -> float:
        """计算性能指标"""
        try:
            # 从结果中提取性能指标
            if "return" in outcome:
                return float(outcome["return"])
            elif "profit_loss" in outcome:
                return float(outcome["profit_loss"])
            elif "success" in outcome:
                return 1.0 if outcome["success"] else 0.0
            else:
                return 0.0
                
        except (ValueError, TypeError, KeyError):
            return 0.0
    
    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self.cache:
            return False
        
        cache_time = self.cache[key]["timestamp"]
        return (datetime.now() - cache_time).seconds < self.cache_timeout
    
    def _cache_data(self, key: str, data: Any) -> None:
        """缓存数据"""
        self.cache[key] = {
            "data": data,
            "timestamp": datetime.now()
        }