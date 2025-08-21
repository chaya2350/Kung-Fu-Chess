#ifndef SCORE_HPP
#define SCORE_HPP

#include "Listener.hpp"
#include "Publisher.hpp"
#include <string>

class Score : public Listener {
public:
    Score(const std::string& color, Publisher* publisher)
        : _score(0) {
        publisher->new_listener(color, "score", this);
    }

    void listening(int points) override {
        _score += points;
    }

    int get_score() const {
        return _score;
    }

protected:
    int _score;
};

#endif // SCORE_HPP
