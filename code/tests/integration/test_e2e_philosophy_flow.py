
"""ThinkLab 哲学探索完整流程 E2E 测试。

测试流程：
1. 创建哲学探索
2. 获取哲学视角
3. 选择斯多葛主义视角
4. 进行第一轮对话
5. 进行第二轮对话
6. 生成结构化总结
7. 查询总结记录
8. 总结后继续对话
"""


def get_session_id(data):
    """从接口返回结果中获取探索 ID。"""
    session_id = data.get("id") or data.get("session_id")

    assert session_id, (
        f"创建探索后没有找到探索 ID，实际返回内容：{data}"
    )

    return session_id


def test_complete_philosophy_exploration_flow(api_client):
    """验证用户从创建探索到总结后继续对话的完整流程。"""

    # E2E-01：创建哲学探索
    create_response = api_client.post(
        "/api/sessions",
        json={
            "question": "我应该如何面对未来的不确定性？"
        }
    )

    assert create_response.status_code == 201

    session_data = create_response.json()
    session_id = get_session_id(session_data)

    # E2E-02：获取哲学视角
    lenses_response = api_client.get(
        f"/api/sessions/{session_id}/lenses"
    )

    assert lenses_response.status_code == 200

    lenses = lenses_response.json()

    # 创建探索后应该能够获取三个哲学视角
    assert isinstance(lenses, list)
    assert len(lenses) >= 3

    # E2E-03：选择斯多葛主义视角
    select_response = api_client.post(
        f"/api/sessions/{session_id}/lens",
        json={
            "lens": "stoic",
            "keep_history": False
        }
    )

    assert select_response.status_code == 200

    # E2E-04：进行第一轮对话
    first_chat_response = api_client.post(
        f"/api/sessions/{session_id}/messages",
        json={
            "content": "如果我无法控制结果，还应该努力吗？"
        }
    )

    assert first_chat_response.status_code == 200

    first_chat_data = first_chat_response.json()

    assert "user_message" in first_chat_data
    assert "agent_message" in first_chat_data

    first_answer = first_chat_data["agent_message"].get("content", "")

    assert isinstance(first_answer, str)
    assert first_answer.strip() != ""

    # E2E-05：进行第二轮对话
    second_chat_response = api_client.post(
        f"/api/sessions/{session_id}/messages",
        json={
            "content": "那么，我应该怎样区分自己能控制和不能控制的事情？"
        }
    )

    assert second_chat_response.status_code == 200

    second_chat_data = second_chat_response.json()

    assert "user_message" in second_chat_data
    assert "agent_message" in second_chat_data

    second_answer = second_chat_data["agent_message"].get("content", "")

    assert isinstance(second_answer, str)
    assert second_answer.strip() != ""

    # E2E-06：生成结构化总结
    summary_response = api_client.post(
        f"/api/sessions/{session_id}/summaries"
    )

    assert summary_response.status_code == 201

    summary_data = summary_response.json()

    assert isinstance(summary_data, dict)
    assert len(summary_data) > 0

    # E2E-07：查询总结记录
    summaries_response = api_client.get(
        f"/api/sessions/{session_id}/summaries"
    )

    assert summaries_response.status_code == 200

    summaries = summaries_response.json()

    assert isinstance(summaries, list)
    assert len(summaries) >= 1

    # E2E-08：生成总结后继续对话
    continue_chat_response = api_client.post(
        f"/api/sessions/{session_id}/messages",
        json={
            "content": "经过刚才的讨论，我应该怎样把这个想法应用到日常生活中？"
        }
    )

    assert continue_chat_response.status_code == 200

    continue_chat_data = continue_chat_response.json()

    assert "user_message" in continue_chat_data
    assert "agent_message" in continue_chat_data

    continue_answer = continue_chat_data["agent_message"].get("content", "")

    assert isinstance(continue_answer, str)
    assert continue_answer.strip() != ""

    # E2E-09：再次查询探索，确认会话仍然存在
    detail_response = api_client.get(
        f"/api/sessions/{session_id}"
    )

    assert detail_response.status_code == 200
