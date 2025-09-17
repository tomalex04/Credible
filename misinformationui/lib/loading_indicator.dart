// loading_indicator.dart
import 'dart:async';
import 'package:flutter/material.dart';

class LoadingIndicator extends StatefulWidget {
  /// When true, the indicator will finish the current step (show its tick)
  /// and then stop looping.
  final bool isCompleted;

  /// How long the spinner shows for each step.
  final Duration spinnerDuration;

  /// How long the tick remains visible before moving to next step.
  final Duration tickDuration;

  const LoadingIndicator({
    super.key,
    required this.isCompleted,
    this.spinnerDuration = const Duration(seconds: 5),
    this.tickDuration = const Duration(milliseconds: 1500),
  });

  @override
  State<LoadingIndicator> createState() => _LoadingIndicatorState();
}

class _LoadingIndicatorState extends State<LoadingIndicator> {
  final List<String> _steps = const [
    'Processing...',
    'Preprocessing the query...',
    'Geolocating...',
    'Fetching news...',
    'Analysing bias in news articles...',
  ];

  int _currentStep = 0;
  bool _showTick = false;

  // Control flags for the async loop
  bool _running = false;
  bool _stopRequested = false;

  @override
  void initState() {
    super.initState();
    _startLoop();
  }

  void _startLoop() {
    // Ensure we don't spawn multiple loops
    if (_running) return;
    _stopRequested = false;
    _runLoop();
  }

  Future<void> _runLoop() async {
    _running = true;
    final spinnerDelay = widget.spinnerDuration;
    final tickDelay = widget.tickDuration;

    while (mounted && !_stopRequested) {
      // Go through all steps sequentially (this completes one full cycle)
      for (int i = 0; i < _steps.length; i++) {
        if (!mounted || _stopRequested) break;

        // show spinner for this step
        setState(() {
          _currentStep = i;
          _showTick = false;
        });

        // wait spinner time
        await Future.delayed(spinnerDelay);
        if (!mounted) break;

        // if parent requested completion while spinner ran, show tick then stop
        if (widget.isCompleted) {
          setState(() => _showTick = true);
          _stopRequested = true;
          break;
        }

        // show tick for this step
        setState(() => _showTick = true);

        // wait tick time
        await Future.delayed(tickDelay);
        if (!mounted) break;

        // if parent requested completion during tick, stop after this tick
        if (widget.isCompleted) {
          _stopRequested = true;
          break;
        }
      }

      // If stop requested, break out of the outer while
      if (_stopRequested || !mounted) break;

      // Completed all steps — loop again from step 0
      // continue while loop -> next for-loop iteration restarts steps
    }

    // Ensure final UI shows tick on whatever the currentStep was
    if (mounted) {
      setState(() => _showTick = true);
    }
    _running = false;
  }

  @override
  void didUpdateWidget(covariant LoadingIndicator oldWidget) {
    super.didUpdateWidget(oldWidget);

    // If parent toggles completion on, request stop so loop finishes current step
    if (!oldWidget.isCompleted && widget.isCompleted) {
      _stopRequested = true;
    }

    // If parent re-enables (isCompleted went false) restart loop if not running
    if (oldWidget.isCompleted && !widget.isCompleted) {
      _stopRequested = false;
      if (!_running) _startLoop();
    }
  }

  @override
  void dispose() {
    _stopRequested = true;
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final String text = _steps[_currentStep];

    // Single Row — only the text and icon inside AnimatedSwitchers change.
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Animated replace of text (one-line only)
        AnimatedSwitcher(
          duration: const Duration(milliseconds: 300),
          transitionBuilder: (child, animation) =>
              FadeTransition(opacity: animation, child: child),
          child: Text(
            text,
            key: ValueKey<int>(_currentStep),
            style: const TextStyle(
              color: Colors.white,
              fontSize: 16,
            ),
          ),
        ),
        const SizedBox(width: 10),
        // Animated replace of spinner <-> tick
        AnimatedSwitcher(
          duration: const Duration(milliseconds: 250),
          transitionBuilder: (child, animation) =>
              ScaleTransition(scale: animation, child: child),
          child: _showTick
              ? const Icon(
                  Icons.check,
                  key: ValueKey('tick'),
                  color: Colors.green,
                  size: 20,
                )
              : const SizedBox(
                  key: ValueKey('spinner'),
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                  ),
                ),
        ),
      ],
    );
  }
}
