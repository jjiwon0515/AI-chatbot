<script setup>
import { ref, nextTick } from 'vue'
import suicon from './assets/icon.png'
import sulogo from './assets/logo.png'
import './ChatBot.css'

const message = ref('')
const userMessages = ref([])
const botReplies = ref([])
const selectionTexts = ref([])
const messageContainer = ref(null)

const restaurants = ref([])  // 데이터베이스에서 가져온 restaurant 데이터를 저장

// 사전 정의된 응답
const predefinedReplies = {
  '점심 메뉴 추천': '오늘의 점심 추천은 김치찌개, 제육볶음, 샐러드입니다!',
  '학사일정': '2025학년도 1학기 개강: 3월 3일\n중간고사: 4월 22일 ~ 26일\n기말고사: 6월 10일 ~ 14일입니다.',
  '커리큘럼': '삼육대학교 커리큘럼은 각 학과별로 다르며, 학교 홈페이지에서 확인하실 수 있습니다.',
  '졸업요건': '졸업을 위해서는 전공 이수 학점과 교양 과목을 포함한 총 130학점 이상이 필요합니다.',
}

// 메시지 상태 관리
const sendMessage = async () => {
  const text = message.value.trim()
  if (text) {
    userMessages.value.push(text)
    selectionTexts.value.push('')
    botReplies.value.push('')
    const currentIndex = botReplies.value.length - 1
    message.value = ''
    await nextTick()
    scrollToBottom()

    await fetchGptReply(text, currentIndex)
  }
}

// 버튼 클릭시 사전 정의된 응답
const handleSelection = async (label) => {
  userMessages.value.push(label)
  selectionTexts.value.push(label)
  const reply = predefinedReplies[label] || '죄송합니다. 해당 항목에 대한 정보가 없습니다.'
  botReplies.value.push(reply)
  await nextTick()
  scrollToBottom()
}

// OpenAI API를 통해 답변 받기
// OpenAI GPT 응답을 Flask RAG API로부터 받기
const fetchGptReply = async (prompt, index) => {
  try {
    const response = await fetch('http://localhost:8081/api/ask', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },  
      body: JSON.stringify({ question: prompt })
    })

    const data = await response.json()
    const reply = data.answer || '답변을 불러오지 못했습니다.'
    botReplies.value[index] = reply
    await nextTick()
    scrollToBottom()
  } catch (err) {
    console.error(err)
    botReplies.value[index] = '⚠️ 서버 오류가 발생했습니다.'
  }
}


// 메시지 스크롤 자동화
const scrollToBottom = () => {
  if (messageContainer.value) {
    messageContainer.value.scrollTop = messageContainer.value.scrollHeight
  }
}

</script>

<template>
  <div class="chatbot-container">
    <div class="chatbot-header">
      <img :src="sulogo" alt="로고" class="header-icon" />
    </div>

    <div class="messages" ref="messageContainer">
      <div class="bot-message-container">
        <img :src="suicon" alt="캐릭터" class="bot-icon" />
        <div class="bot-message">
          <p>
            안녕하세요!<br />
            삼육대학교 생성형 AI 챗봇 수아입니다 :)<br /><br />
            무엇이 궁금하신가요?<br />
            질문을 구체적으로 해주시면 더 정확한 답변을 드릴 수 있어요.<br />
          </p>
        </div>
      </div>

      <!-- restaurants 데이터를 화면에 출력 -->
      <div v-if="restaurants.length > 0">
        <h2>추천 맛집:</h2>
        <ul>
          <li v-for="restaurant in restaurants" :key="restaurant.id">
            {{ restaurant.name }} - {{ restaurant.category }} - {{ restaurant.description }}
          </li>
        </ul>
      </div>

      <div class="button-group">
        <button @click="handleSelection('점심 메뉴 추천')">점심 메뉴 추천</button>
        <button @click="handleSelection('학사일정')">학사일정</button>
        <button @click="handleSelection('커리큘럼')">커리큘럼</button>
        <button @click="handleSelection('졸업요건')">졸업요건</button>
      </div>

      <div v-for="(msg, index) in userMessages" :key="index">
        <div class="selection-text" v-if="selectionTexts[index]">
          ‘{{ selectionTexts[index] }}’을 선택하셨습니다.
        </div>

        <div class="user-message-wrapper">
          <div class="user-message">{{ msg }}</div>
        </div>

        <div class="bot-message-container" v-if="botReplies[index] !== undefined">
          <img :src="suicon" alt="캐릭터" class="bot-icon" />
          <div class="bot-message">{{ botReplies[index] || ' ' }}</div>
        </div>
      </div>
    </div>

    <div class="input-area">
      <input v-model="message" type="text" placeholder="메시지 보내기" @keyup.enter="sendMessage" />
      <button @click="sendMessage">➤</button>
    </div>
  </div>
</template>
