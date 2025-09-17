import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:http/http.dart' as http;
import 'loading_indicator.dart';
import 'package:flutter_linkify/flutter_linkify.dart';
import 'package:url_launcher/url_launcher.dart';

class Message {
  final String text;
  final bool isUser;
  final bool isPreFormatted;
  final bool isLoading;
  final int? loadingStep;
  final bool? isStepCompleted;

  Message({
    required this.text,
    required this.isUser,
    this.isPreFormatted = false,
    this.isLoading = false,
    this.loadingStep,
    this.isStepCompleted,
  });
}

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final List<Message> _messages = [];
  final TextEditingController _controller = TextEditingController();
  bool _isBackgroundBlurred = false;
  final ScrollController _scrollController = ScrollController();

Future<void> _sendMessage() async {
  final query = _controller.text.trim();
  if (query.isEmpty) return;

  setState(() {
    _isBackgroundBlurred = true;
    _messages.add(Message(text: query, isUser: true));
    _messages.add(Message(text: '', isUser: false, isLoading: true));
    _controller.clear();
  });
  _scrollToBottom();

  final loadingMessageIndex = _messages.length - 1;

  try {
    final response = await http.post(
      Uri.parse('http://localhost:5000/api/detect'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'query': query}),
    );
    final data = jsonDecode(response.body);

    setState(() {
      _messages[loadingMessageIndex] = Message(
        text: '',
        isUser: false,
        isLoading: true,
        isStepCompleted: true,
      );
    });

    await Future.delayed(const Duration(milliseconds: 600));

    setState(() {
      if (loadingMessageIndex < _messages.length) {
        _messages.removeAt(loadingMessageIndex);
      }

      // --- STEP 1: Show raw JSON ---
      // _messages.add(Message(
      //   text: jsonEncode(data),
      //   isUser: false,
      //   isPreFormatted: true,
      // ));

      // --- STEP 2: Show only values ---
      String valuesText = '';
      if (data is Map) {
        valuesText = data.values.map((v) => v.toString()).join('\n\n');
      } else if (data is List) {
        valuesText = data.map((v) => v.toString()).join('\n\n');
      } else {
        valuesText = data.toString();
      }

      _messages.add(Message(
        text: valuesText,
        isUser: false,
        isPreFormatted: true,
      ));
    });
  } catch (e) {
    setState(() {
      if (loadingMessageIndex < _messages.length) {
        _messages[loadingMessageIndex] = Message(
          text: '',
          isUser: false,
          isLoading: true,
          isStepCompleted: true,
        );
      }
    });
    await Future.delayed(const Duration(milliseconds: 600));
    setState(() {
      if (loadingMessageIndex < _messages.length) {
        _messages.removeAt(loadingMessageIndex);
      }
      // Do not add any hardcoded error message.
    });
  }
  _scrollToBottom();
}

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          Expanded(
            child: Stack(
              children: [
                if (!_isBackgroundBlurred)
                  Center(
                    child: SizedBox(
                      width: MediaQuery.of(context).size.width * 0.8,
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              crossAxisAlignment: CrossAxisAlignment.center,
                              children: [
                                Text(
                                  'Hey,',
                                  style: GoogleFonts.courierPrime(
                                    color: Colors.white,
                                    fontSize: 64,
                                    fontWeight: FontWeight.bold,
                                  ),
                                  textAlign: TextAlign.start,
                                ),
                                const SizedBox(height: 10), // Add some spacing
                                Text(
                                  'Discover misinformations around you...',
                                  style: GoogleFonts.courierPrime(
                                    color: Colors.white,
                                    fontSize: 32,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                if (_isBackgroundBlurred)
                  Expanded(
                    child: ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.all(15),
                      itemCount: _messages.length,
                      itemBuilder: (context, index) {
                        final message = _messages[index];
                        return MessageBubble(message: message);
                      },
                    ),
                  ),
              ],
            ),
          ),
          Center(
            child: Container(
              width: MediaQuery.of(context).size.width * 0.6,
              margin: const EdgeInsets.all(16.0),
              decoration: BoxDecoration(
                color: Colors.grey[800]!.withOpacity(0.7),
                borderRadius: BorderRadius.circular(30),
                border: Border.all(
                  color: Colors.grey[600]!,
                  width: 1,
                ),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 15),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      cursorColor: Colors.white,
                      style: const TextStyle(color: Colors.white),
                      decoration: const InputDecoration(
                        hintText: 'Type an info to verify...',
                        hintStyle: TextStyle(color: Colors.grey),
                        border: InputBorder.none,
                      ),
                      onSubmitted: (_) => _sendMessage(),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.send, color: Colors.white),
                    onPressed: _sendMessage,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}



class MessageBubble extends StatelessWidget {
  final Message message;

  const MessageBubble({super.key, required this.message});

  Future<void> _onOpen(LinkableElement link) async {
    if (await canLaunchUrl(Uri.parse(link.url))) {
      await launchUrl(Uri.parse(link.url));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: message.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.8,
        ),
        margin: const EdgeInsets.only(bottom: 4),
        padding: const EdgeInsets.all(10),
        decoration: message.isUser
            ? BoxDecoration(
                color: const Color(0xFF414141),
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(20),
                  topRight: const Radius.circular(20),
                  bottomLeft: Radius.circular(message.isUser ? 15 : 5),
                  bottomRight: Radius.circular(message.isUser ? 5 : 15),
                ),
              )
            : null,
        child: message.isLoading
            ? LoadingIndicator(
                isCompleted: message.isStepCompleted ?? false,
              )
            : message.isPreFormatted
                ? SelectableLinkify(
                    text: message.text,
                    onOpen: _onOpen,
                    linkStyle: const TextStyle(
                      color: Colors.blueAccent,
                      decoration: TextDecoration.underline
                    ),
                    style: const TextStyle(
                      fontFamily: 'Montserrat',
                      fontSize: 16,
                      color: Colors.white,
                    ),
                  )
                : Text(
                    message.text,
                    style: const TextStyle(color: Colors.white),
                  ),
      ),
    );
  }
}