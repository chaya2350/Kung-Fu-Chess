#ifndef SCORE_HPP
#define SCORE_HPP

#include "Listener.hpp"
#include "Publisher.hpp"
#include <string>


class Score : public Listener {
public:
    Score(const std::string& color, Publisher* publisher)
        : Listener(color, "score", publisher), _score(0) {}

    // Required by Listener interface
    void listening(const std::string& message) override {
        // Try to parse message as int points
        try {
            int points = std::stoi(message);
            _score += points;
        } catch (...) {
            // Ignore invalid messages
        }
    }

    void add(int points) {
        _score += points;
    }

    int get_score() const {
        return _score;
    }

protected:
    int _score;
};

#endif // SCORE_HPP
