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
#include "ResponseFrame_m.h"

namespace smile {
namespace algorithm {
namespace ss_twr {

class MobileApplication : public smile::IdealApplication
{
 public:
  MobileApplication() = default;
  MobileApplication(const MobileApplication& source) = delete;
  MobileApplication(MobileApplication&& source) = delete;
  ~MobileApplication();

  MobileApplication& operator=(const MobileApplication& source) = delete;
  MobileApplication& operator=(MobileApplication&& source) = delete;

 private:
  void initialize(int stage) override;

  void handleSelfMessage(cMessage* message) override;

  void handleIncommingMessage(cMessage* newMessage) override;

  void handleTxCompletionSignal(const smile::IdealTxCompletion& completion) override;

  void handleRxCompletionSignal(const smile::IdealRxCompletion& completion) override;

  void startRanging();

  void handleResponseFrame(std::unique_ptr<ResponseFrame> frame);

  static const std::string pollFrameName;
  static const std::string responseFrameName;

  std::unique_ptr<cMessage> rxTimeoutTimerMessage;
  std::vector<inet::MACAddress> anchorAddresses;

  SimTime pollTxBeginTimestamp{0};
  SimTime responseRxBeginTimestamp{0};
  smile::Logger::Handle framesLog;
  unsigned long sequenceNumber{0};
};

}  // namespace ss_twr
}  // namespace algorithm
}  // namespace smile