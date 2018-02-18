//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see http://www.gnu.org/licenses/.
//

#pragma once

#include <IdealApplication.h>
#include <Logger.h>
#include "Frame_m.h"

namespace smile {
namespace algorithm {
namespace ss_twr {

class AnchorApplication : public smile::IdealApplication
{
 public:
  AnchorApplication() = default;
  AnchorApplication(const AnchorApplication& source) = delete;
  AnchorApplication(AnchorApplication&& source) = delete;
  ~AnchorApplication() = default;

  AnchorApplication& operator=(const AnchorApplication& source) = delete;
  AnchorApplication& operator=(AnchorApplication&& source) = delete;

 private:
  void initialize(int stage) override;

  void handleIncommingMessage(cMessage* newMessage) override;

  void handleTxCompletionSignal(const smile::IdealTxCompletion& completion) override;

  void handleRxCompletionSignal(const smile::IdealRxCompletion& completion) override;

  void handlePollFrame(std::unique_ptr<Frame> pollFrame);

  static const std::string pollFrameName;
  static const std::string responseFrameName;

  SimTime messageProcessingTime;
  SimTime responseTxClockTime;
  smile::Logger* framesLog{nullptr};
};

}  // namespace ss_twr
}  // namespace algorithm
}  // namespace smile
