import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'https://nithiyanandham15-voicecallendpoint.hf.space';

function App() {
  const [isCallActive, setIsCallActive] = useState(false);
  const [status, setStatus] = useState({ type: '', text: 'Ready to connect' });
  const [conversationHistory, setConversationHistory] = useState([]);
  const [error, setError] = useState('');
  const [twilioConfig, setTwilioConfig] = useState({
    accountSid: '',
    authToken: '',
    phoneNumber: ''
  });
  const [twilioStatus, setTwilioStatus] = useState({ configured: false, phoneNumber: '' });
  const [showTwilioForm, setShowTwilioForm] = useState(false);
  const [copied, setCopied] = useState(false);
  const recognitionRef = useRef(null);
  const synthesisRef = useRef(null);
  const conversationAreaRef = useRef(null);
  const isCallActiveRef = useRef(false);
  const isSpeakingRef = useRef(false);
  const speechStartTimeRef = useRef(null);
  const speechTimeoutRef = useRef(null);
  const currentUtteranceRef = useRef(null);

  // Sync ref with state
  useEffect(() => {
    isCallActiveRef.current = isCallActive;
  }, [isCallActive]);

  // Load conversation history on mount
  useEffect(() => {
    const loadHistory = () => {
      const savedHistory = localStorage.getItem('voiceAiConversation');
      if (savedHistory) {
        try {
          setConversationHistory(JSON.parse(savedHistory));
        } catch (e) {
          console.error('Error loading conversation history:', e);
        }
      }
    };

    const checkConn = async () => {
      try {
        const response = await fetch(`${API_URL}/api/status`);
        if (!response.ok) {
          throw new Error('Server not responding');
        }
        updateStatus('active', 'Connected');
      } catch (error) {
        setError('Cannot connect to server. Please check your connection.');
        updateStatus('', 'Disconnected');
      }
    };

    const loadTwilioStatus = async () => {
      try {
        // Always reset connection status on page load
        setTwilioStatus({ configured: false, phoneNumber: '' });
        setTwilioConfig({ accountSid: '', authToken: '', phoneNumber: '' });
        localStorage.removeItem('twilioCredentials');
        setShowTwilioForm(true);
        
        // Check backend status (but don't auto-connect)
        const response = await fetch(`${API_URL}/api/twilio/credentials`);
        const data = await response.json();
        if (data.status === 'success' && data.configured) {
          // Backend has credentials, but we still show as not connected
          // User needs to manually connect again after page refresh
          // Load stored credentials for display purposes only
          const storedCredentials = localStorage.getItem('twilioCredentials');
          if (storedCredentials) {
            try {
              const creds = JSON.parse(storedCredentials);
              setTwilioConfig({
                accountSid: creds.accountSid || '',
                authToken: creds.authToken || '••••••••••••••••',
                phoneNumber: creds.phoneNumber || ''
              });
            } catch (e) {
              console.error('Error parsing stored credentials:', e);
            }
          }
        }
      } catch (e) {
        console.error('Error loading Twilio status:', e);
        // On error, ensure everything is reset
        setTwilioStatus({ configured: false, phoneNumber: '' });
        setTwilioConfig({ accountSid: '', authToken: '', phoneNumber: '' });
        localStorage.removeItem('twilioCredentials');
        setShowTwilioForm(true);
      }
    };

    loadHistory();
    checkConn();
    loadTwilioStatus();
    initSpeechRecognition();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Scroll to bottom when new messages are added
  useEffect(() => {
    if (conversationAreaRef.current) {
      conversationAreaRef.current.scrollTop = conversationAreaRef.current.scrollHeight;
    }
  }, [conversationHistory]);

  const updateStatus = useCallback((type, text) => {
    setStatus({ type, text });
  }, []);

  const speakText = useCallback((text, onComplete) => {
    if (!synthesisRef.current || !isCallActiveRef.current) {
      console.log('Cannot speak - synthesis not available or call not active');
      return;
    }

    console.log('Speaking text:', text);
    updateStatus('speaking', 'Speaking...');
    isSpeakingRef.current = true;

    synthesisRef.current.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    
    currentUtteranceRef.current = utterance;

    utterance.onstart = () => {
      console.log('TTS started');
      isSpeakingRef.current = true;
      // Keep recognition running in background for barge-in
      if (recognitionRef.current && isCallActiveRef.current) {
        try {
          if (recognitionRef.current.state === 'inactive' || recognitionRef.current.state === 'ended') {
            recognitionRef.current.start();
            console.log('Recognition started in background for barge-in');
          }
        } catch (e) {
          if (e.name !== 'InvalidStateError') {
            console.error('Error starting recognition for barge-in:', e);
          }
        }
      }
    };

    utterance.onend = () => {
      console.log('Speech synthesis ended.');
      isSpeakingRef.current = false;
      currentUtteranceRef.current = null;
      speechStartTimeRef.current = null;
      
      if (isCallActiveRef.current) {
        if (onComplete) {
          onComplete();
        } else {
          updateStatus('listening', 'Listening...');
          setTimeout(() => {
            if (isCallActiveRef.current && recognitionRef.current) {
              try {
                if (recognitionRef.current.state === 'inactive' || recognitionRef.current.state === 'ended') {
                  recognitionRef.current.start();
                }
              } catch (e) {
                if (e.name !== 'InvalidStateError') {
                  console.error('Recognition start error (after speech):', e);
                }
              }
            }
          }, 500);
        }
      }
    };

    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event);
      isSpeakingRef.current = false;
      currentUtteranceRef.current = null;
      speechStartTimeRef.current = null;
      
      if (isCallActiveRef.current) {
        if (onComplete) {
          onComplete();
        } else {
          updateStatus('listening', 'Listening...');
          setTimeout(() => {
            if (isCallActiveRef.current && recognitionRef.current) {
              try {
                recognitionRef.current.start();
              } catch (e) {
                if (e.name !== 'InvalidStateError') {
                  console.error('Recognition start error (after speech error):', e);
                }
              }
            }
          }, 500);
        }
      }
    };

    synthesisRef.current.speak(utterance);
  }, [updateStatus]);

  const processUserMessage = useCallback(async (userText) => {
    if (!userText.trim() || !isCallActiveRef.current) {
      console.log('Skipping - empty text or call not active');
      return;
    }

    console.log('=== Processing User Message ===');
    console.log('User text:', userText);
    console.log('Call active:', isCallActiveRef.current);

    setConversationHistory(prev => {
      const newMessage = {
        type: 'user',
        text: userText,
        timestamp: new Date().toISOString()
      };
      const updated = [...prev, newMessage];
      localStorage.setItem('voiceAiConversation', JSON.stringify(updated));
      return updated;
    });

    updateStatus('processing', 'Processing your message...');

    if (recognitionRef.current && isCallActiveRef.current) {
      try {
        recognitionRef.current.stop();
        console.log('Recognition stopped for processing');
      } catch (e) {
        console.error('Error stopping recognition:', e);
      }
    }

    try {
      console.log('Sending to LLM API...');
      const response = await fetch(`${API_URL}/api/chat?message=${encodeURIComponent(userText)}`);
      const data = await response.json();

      console.log('LLM Response:', data);

      if (data.status === 'success') {
        const aiResponse = data.response;
        console.log('AI Response text:', aiResponse);

        setConversationHistory(prev => {
          const newMessage = {
            type: 'ai',
            text: aiResponse,
            timestamp: new Date().toISOString()
          };
          const updated = [...prev, newMessage];
          localStorage.setItem('voiceAiConversation', JSON.stringify(updated));
          return updated;
        });
        console.log('AI message added to UI');

        speakText(aiResponse, () => {
          console.log('Speech completed, resuming listening...');
          if (isCallActiveRef.current && recognitionRef.current) {
            updateStatus('listening', 'Listening...');
            setTimeout(() => {
              try {
                console.log('Restarting recognition...');
                recognitionRef.current.start();
                console.log('Recognition restarted successfully');
              } catch (e) {
                if (e.name !== 'InvalidStateError') {
                  console.error('Recognition start error:', e);
                } else {
                  console.log('Recognition already started');
                }
              }
            }, 1000);
          } else {
            console.log('Not resuming - call not active or recognition not available');
          }
        });
      } else {
        throw new Error(data.error || 'Unknown error');
      }
    } catch (error) {
      setError(`Error: ${error.message}`);
      const errorMsg = 'I apologize, but I encountered an error. Please try again.';
      setConversationHistory(prev => {
        const newMessage = {
          type: 'ai',
          text: errorMsg,
          timestamp: new Date().toISOString()
        };
        const updated = [...prev, newMessage];
        localStorage.setItem('voiceAiConversation', JSON.stringify(updated));
        return updated;
      });

      speakText(errorMsg, () => {
        if (isCallActiveRef.current && recognitionRef.current) {
          updateStatus('listening', 'Listening...');
          setTimeout(() => {
            try {
              recognitionRef.current.start();
            } catch (e) {
              if (e.name !== 'InvalidStateError') {
                console.error('Recognition start error:', e);
              }
            }
          }, 500);
        }
      });
    }
  }, [updateStatus, speakText]);


  const initSpeechRecognition = useCallback(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = async (event) => {
        const transcript = event.results[event.results.length - 1][0].transcript;
        console.log('Speech recognized:', transcript);
        console.log('Call active:', isCallActiveRef.current);
        console.log('Is speaking:', isSpeakingRef.current);
        
        if (transcript.trim() && isCallActiveRef.current) {
          // Track speech start time for barge-in detection
          if (!speechStartTimeRef.current) {
            speechStartTimeRef.current = Date.now();
            console.log('Speech started, tracking for barge-in...');
          }
          
          // Check if user has been speaking for more than 2 seconds
          const speechDuration = Date.now() - speechStartTimeRef.current;
          console.log(`Speech duration: ${speechDuration}ms`);
          
          if (speechDuration >= 2000 && isSpeakingRef.current) {
            // User has been speaking for 2+ seconds while AI is speaking - interrupt!
            console.log('Barge-in detected! Stopping TTS and processing user speech...');
            if (synthesisRef.current) {
              synthesisRef.current.cancel();
              isSpeakingRef.current = false;
            }
            if (speechTimeoutRef.current) {
              clearTimeout(speechTimeoutRef.current);
            }
            speechStartTimeRef.current = null;
            
            // Process the user message
            await processUserMessage(transcript);
          } else if (!isSpeakingRef.current) {
            // AI is not speaking, process normally
            speechStartTimeRef.current = null;
            await processUserMessage(transcript);
          }
          // If AI is speaking but speech is less than 2 seconds, wait for more speech
        }
      };
      
      recognitionRef.current.onspeechstart = () => {
        console.log('Speech start detected');
        if (!speechStartTimeRef.current) {
          speechStartTimeRef.current = Date.now();
        }
      };
      
      recognitionRef.current.onspeechend = () => {
        console.log('Speech end detected');
        // Reset speech tracking after a delay
        if (speechTimeoutRef.current) {
          clearTimeout(speechTimeoutRef.current);
        }
        speechTimeoutRef.current = setTimeout(() => {
          speechStartTimeRef.current = null;
          console.log('Speech tracking reset');
        }, 500);
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error event:', event);
        if (event.error === 'no-speech') {
          if (isCallActiveRef.current) {
            console.log('No speech detected, restarting recognition...');
            setTimeout(() => {
              try {
                recognitionRef.current.start();
              } catch (e) {
                if (e.name !== 'InvalidStateError') {
                  console.error('Recognition restart error (no-speech):', e);
                }
              }
            }, 300);
          }
          return;
        }
        if (event.error === 'aborted') {
          console.log('Recognition aborted intentionally.');
          return;
        }
        setError(`Speech recognition error: ${event.error}`);
        console.error('Speech recognition error:', event.error);
        if (isCallActiveRef.current && event.error !== 'not-allowed') {
          console.log('Attempting to restart recognition after error...');
          setTimeout(() => {
            try {
              recognitionRef.current.start();
            } catch (e) {
              if (e.name !== 'InvalidStateError') {
                console.error('Recognition restart error (general):', e);
              }
            }
          }, 1000);
        }
      };

      recognitionRef.current.onend = () => {
        console.log('Recognition ended. isCallActive:', isCallActiveRef.current);
        if (isCallActiveRef.current) {
          setTimeout(() => {
            try {
              recognitionRef.current.start();
            } catch (e) {
              if (e.name !== 'InvalidStateError') {
                console.error('Recognition auto-restart error:', e);
              }
            }
          }, 300);
        }
      };
    } else {
      setError('Speech recognition not supported. Please use Chrome or Edge browser.');
      return false;
    }

    if ('speechSynthesis' in window) {
      synthesisRef.current = window.speechSynthesis;
    } else {
      setError('Speech synthesis not supported.');
      return false;
    }

    return true;
  }, [processUserMessage]);

  const startCall = useCallback(async () => {
    console.log('Starting call...');
    if (!recognitionRef.current || !synthesisRef.current) {
      if (!initSpeechRecognition()) {
        return;
      }
    }

    // Clear conversation history when starting a new call
    setConversationHistory([]);
    localStorage.removeItem('voiceAiConversation');
    console.log('Conversation history cleared for new call');

    setIsCallActive(true);
    isCallActiveRef.current = true;
    updateStatus('listening', 'Listening...');

    // Start with welcome message
    setConversationHistory(prev => {
      const welcomeMsg = 'Hello! I\'m your AI assistant. How can I help you today?';
      const newMessage = {
        type: 'ai',
        text: welcomeMsg,
        timestamp: new Date().toISOString()
      };
      const updated = [newMessage];
      localStorage.setItem('voiceAiConversation', JSON.stringify(updated));
      
      // Speak welcome message and start listening
      setTimeout(() => {
        speakText(welcomeMsg, () => {
          console.log('Welcome message spoken, starting recognition...');
          if (isCallActiveRef.current && recognitionRef.current) {
            updateStatus('listening', 'Listening...');
            setTimeout(() => {
              try {
                console.log('Starting recognition after welcome...');
                recognitionRef.current.start();
                console.log('Recognition started successfully');
              } catch (e) {
                if (e.name !== 'InvalidStateError') {
                  console.error('Recognition start error:', e);
                } else {
                  console.log('Recognition already started');
                }
              }
            }, 500);
          }
        });
      }, 100);
      
      return updated;
    });
  }, [initSpeechRecognition, speakText, updateStatus]);

  const toggleCall = useCallback(async () => {
    if (!isCallActive) {
      await startCall();
    } else {
      endCall();
    }
  }, [isCallActive, startCall]);

  const endCall = useCallback(() => {
    console.log('Ending call...');
    setIsCallActive(false);
    isCallActiveRef.current = false;
    updateStatus('', 'Call ended');

    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch (e) {
        try {
          recognitionRef.current.stop();
        } catch (e2) {
          console.error('Error stopping recognition:', e2);
        }
      }
    }

    if (synthesisRef.current) {
      synthesisRef.current.cancel();
      isSpeakingRef.current = false;
      currentUtteranceRef.current = null;
    }
    
    // Clear speech tracking
    speechStartTimeRef.current = null;
    if (speechTimeoutRef.current) {
      clearTimeout(speechTimeoutRef.current);
    }

    setConversationHistory(prev => {
      const newMessage = {
        type: 'ai',
        text: 'Call ended. Thank you for using Voice AI Assistant.',
        timestamp: new Date().toISOString()
      };
      const updated = [...prev, newMessage];
      localStorage.setItem('voiceAiConversation', JSON.stringify(updated));
      return updated;
    });
  }, [updateStatus]);

  const copyWebhookUrl = () => {
    const webhookUrl = `${API_URL}/api/voice/incoming`;
    navigator.clipboard.writeText(webhookUrl).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(err => {
      console.error('Failed to copy:', err);
    });
  };

  const handleTwilioSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validate credentials format
    if (!twilioConfig.accountSid.trim().startsWith('AC') || twilioConfig.accountSid.trim().length < 30) {
      setError('Invalid Account SID format. It should start with "AC" and be at least 30 characters.');
      return;
    }

    // Check if auth token is masked (stored credentials)
    const isMaskedToken = twilioConfig.authToken.startsWith('••••');
    const authTokenToSend = isMaskedToken ? '' : twilioConfig.authToken.trim();
    
    if (isMaskedToken) {
      setError('Please enter a new Auth Token to update credentials. The current token is masked for security.');
      return;
    }
    
    if (!authTokenToSend || authTokenToSend.length < 30) {
      setError('Invalid Auth Token format. It should be at least 30 characters.');
      return;
    }

    if (!twilioConfig.phoneNumber.trim().startsWith('+')) {
      setError('Invalid Phone Number format. It should start with "+" (e.g., +1234567890).');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('account_sid', twilioConfig.accountSid.trim());
      formData.append('auth_token', authTokenToSend);
      formData.append('phone_number', twilioConfig.phoneNumber.trim());

      const response = await fetch(`${API_URL}/api/twilio/credentials`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (data.status === 'success') {
        // Store credentials in localStorage (masked for security)
        const credentialsToStore = {
          accountSid: twilioConfig.accountSid.trim(),
          authToken: '••••••••••••••••', // Masked token
          phoneNumber: twilioConfig.phoneNumber.trim()
        };
        localStorage.setItem('twilioCredentials', JSON.stringify(credentialsToStore));
        
        setTwilioStatus({
          configured: true,
          phoneNumber: twilioConfig.phoneNumber.trim()
        });
        // Keep credentials in state so they're visible when dropdown is expanded
        setTwilioConfig({
          accountSid: twilioConfig.accountSid.trim(),
          authToken: '••••••••••••••••', // Show masked token
          phoneNumber: twilioConfig.phoneNumber.trim()
        });
        setError('');
        setShowTwilioForm(false); // Hide form after successful connection
        // Don't add system messages to conversation history
      } else {
        setError(data.error || 'Failed to connect to Twilio');
      }
    } catch (error) {
      setError(`Error: ${error.message}`);
    }
  };

  return (
    <div className="app-layout">
      {/* Twilio Settings Sidebar */}
      <div className="twilio-sidebar">
        <div className="sidebar-header">
          <div 
            className="dropdown-header"
            onClick={() => setShowTwilioForm(!showTwilioForm)}
          >
            <div className="dropdown-header-content">
              <div>
                <h2>Twilio Configuration</h2>
                {twilioStatus.configured && (
                  <div className="connection-status">
                    <span className="status-indicator connected"></span>
                    <span>Connected: {twilioStatus.phoneNumber}</span>
                  </div>
                )}
              </div>
              <button 
                className={`dropdown-toggle ${showTwilioForm ? 'expanded' : ''}`}
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowTwilioForm(!showTwilioForm);
                }}
              >
                <svg 
                  width="20" 
                  height="20" 
                  viewBox="0 0 20 20" 
                  fill="none" 
                  xmlns="http://www.w3.org/2000/svg"
                  className="dropdown-icon"
                >
                  <path 
                    d="M5 7.5L10 12.5L15 7.5" 
                    stroke="currentColor" 
                    strokeWidth="2" 
                    strokeLinecap="round" 
                    strokeLinejoin="round"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
        
        {/* Webhook URL Section - Always Visible */}
        <div style={{ 
          padding: '16px', 
          borderTop: '1px solid #e5e7eb',
          borderBottom: '1px solid #e5e7eb'
        }}>
          <label style={{ 
            display: 'block', 
            fontSize: '13px', 
            fontWeight: '600', 
            color: '#374151', 
            marginBottom: '8px' 
          }}>
            Twilio Webhook URL
          </label>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            backgroundColor: '#f9fafb',
            padding: '8px 12px',
            borderRadius: '6px',
            border: '1px solid #e5e7eb'
          }}>
            <input
              type="text"
              readOnly
              value={`${API_URL}/api/voice/incoming`}
              style={{
                flex: 1,
                border: 'none',
                background: 'transparent',
                fontSize: '12px',
                color: '#1f2937',
                outline: 'none',
                fontFamily: 'monospace'
              }}
              onClick={(e) => e.target.select()}
            />
            <button
              type="button"
              onClick={copyWebhookUrl}
              style={{
                padding: '6px 12px',
                backgroundColor: copied ? '#10b981' : '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: '500',
                transition: 'background-color 0.2s',
                whiteSpace: 'nowrap'
              }}
              onMouseEnter={(e) => {
                if (!copied) e.target.style.backgroundColor = '#2563eb';
              }}
              onMouseLeave={(e) => {
                if (!copied) e.target.style.backgroundColor = '#3b82f6';
              }}
            >
              {copied ? '✓ Copied!' : 'Copy'}
            </button>
          </div>
          <p style={{ 
            fontSize: '11px', 
            color: '#6b7280', 
            marginTop: '8px',
            lineHeight: '1.4'
          }}>
            Use this URL in your Twilio phone number's webhook settings (POST method)
          </p>
        </div>

        {showTwilioForm && (
          <>
            <form onSubmit={handleTwilioSubmit} className="twilio-form">
              <div className="form-group">
                <label htmlFor="accountSid">Account SID</label>
                <input
                  type="text"
                  id="accountSid"
                  value={twilioConfig.accountSid}
                  onChange={(e) => setTwilioConfig({ ...twilioConfig, accountSid: e.target.value })}
                  placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="authToken">Auth Token</label>
                <input
                  type="password"
                  id="authToken"
                  value={twilioConfig.authToken}
                  onChange={(e) => setTwilioConfig({ ...twilioConfig, authToken: e.target.value })}
                  placeholder="Your Twilio Auth Token"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="phoneNumber">Phone Number</label>
                <input
                  type="text"
                  id="phoneNumber"
                  value={twilioConfig.phoneNumber}
                  onChange={(e) => setTwilioConfig({ ...twilioConfig, phoneNumber: e.target.value })}
                  placeholder="+1234567890"
                  required
                />
              </div>
              {error && (
                <div className="error-message show" style={{ marginBottom: '16px' }}>{error}</div>
              )}
              <button type="submit" className="connect-button">
                {twilioStatus.configured ? 'Update Connection' : 'Connect to Twilio'}
              </button>
            </form>

            <div className="sidebar-footer">
              <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '16px', textAlign: 'center' }}>
                Get your credentials from <a href="https://console.twilio.com" target="_blank" rel="noopener noreferrer">Twilio Console</a>
              </p>
            </div>
          </>
        )}
        
        {!showTwilioForm && twilioStatus.configured && (
          <div className="sidebar-collapsed-content">
            <p style={{ fontSize: '13px', color: '#6b7280', padding: '16px', textAlign: 'center' }}>
              Click to configure or update Twilio settings
            </p>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="container">
        {/* Header */}
        <div className="header">
          <h1>Voice AI Assistant</h1>
          <p>Intelligent voice-powered conversation system</p>
        </div>

      {/* Status Bar */}
      <div className="status-bar">
        <div className={`status-indicator ${status.type}`}></div>
        <span className="status-text">{status.text}</span>
      </div>

      {/* Main Content */}
      <div className="main-content" ref={conversationAreaRef}>
        <div className="conversation-area">
          {conversationHistory.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">💬</div>
              <div className="empty-state-text">Click the call button to start a conversation</div>
            </div>
          ) : (
            conversationHistory.map((msg, index) => (
              <div key={index} className={`message ${msg.type}`}>
                <div className="message-avatar">
                  {msg.type === 'user' ? '👤' : '🤖'}
                </div>
                <div className="message-content">
                  <div className="message-label">
                    {msg.type === 'user' ? 'You' : 'AI Assistant'}
                  </div>
                  <div className="message-text">{msg.text}</div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Control Panel */}
      <div className="control-panel">
        <div className="call-button-container">
          <button
            className={`call-button ${isCallActive ? 'active' : 'idle'}`}
            onClick={toggleCall}
          >
            📞
          </button>
        </div>
        <div className="info-text">
          {isCallActive ? 'Click again to end the call' : 'Click to start voice conversation (clears history)'}
        </div>
        {error && (
          <div className="error-message show">{error}</div>
        )}
      </div>
      </div>
    </div>
  );
}

export default App;

