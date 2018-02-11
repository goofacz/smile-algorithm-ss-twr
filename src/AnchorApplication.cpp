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

#include "AnchorApplication.h"
#include "Frame_m.h"

#include <CsvLogger.h>
#include <utilities.h>

namespace smile {
namespace algorithm {
namespace ss_twr {

Define_Module(AnchorApplication);

const std::string AnchorApplication::pollFrameName{"POLL"};
const std::string AnchorApplication::responseFrameName{"RESPONSE"};

void AnchorApplication::initialize(int stage)
{
  IdealApplication::initialize(stage);

  if (stage == inet::INITSTAGE_LOCAL) {
    messageProcessingTime = SimTime{par("messageProcessingTime").longValue(), SIMTIME_MS};
  }

  if (stage == inet::INITSTAGE_APPLICATION_LAYER) {
    auto& logger = getLogger();
    const auto handle = logger.obtainHandle("anchors");
    const auto entry = csv_logger::compose(getMacAddress(), getCurrentTruePosition(), messageProcessingTime);
    logger.append(handle, entry);

    framesLog = logger.obtainHandle("anchor_frames");
  }
}

void AnchorApplication::handleIncommingMessage(cMessage* newMessage)
{
  std::unique_ptr<cMessage> message{newMessage};
  handlePollFrame(smile::dynamic_unique_ptr_cast<Frame>(std::move(message)));
}

void AnchorApplication::handleTxCompletionSignal(const smile::IdealTxCompletion& completion)
{
  const auto& frame = completion.getFrame();
  if (responseFrameName == frame->getName()) {
    const auto frame = dynamic_cast<const Frame*>(completion.getFrame());
    if (!frame) {
      throw cRuntimeError{"Received signal for %s message, expected ResponseFrame", frame->getClassName()};
    }

    auto& logger = getLogger();
    const auto entry = smile::csv_logger::compose(getMacAddress(), completion, frame->getSequenceNumber());
    logger.append(framesLog, entry);
  }
  else {
    throw cRuntimeError{"Received TX completion signal for unexpected packet of type %s and name \"%s\"",
                        frame->getClassName(), frame->getName()};
  }
}

void AnchorApplication::handleRxCompletionSignal(const smile::IdealRxCompletion& completion)
{
  const auto& frame = completion.getFrame();
  if (pollFrameName == frame->getName()) {
    const auto& pollRxBeginTimestamp = completion.getOperationBeginClockTimestamp();
    const auto frame = dynamic_cast<const Frame*>(completion.getFrame());
    if (!frame) {
      throw cRuntimeError{"Received signal for %s message, expected PollFrame", frame->getClassName()};
    }

    auto& logger = getLogger();
    const auto entry = smile::csv_logger::compose(getMacAddress(), completion, frame->getSequenceNumber());
    logger.append(framesLog, entry);

    responseTxClockTime = clockTime() + messageProcessingTime;
  }
  else {
    throw cRuntimeError{"Received RX completion signal for unexpected packet of type %s and name \"%s\"",
                        frame->getClassName(), frame->getName()};
  }
}

void AnchorApplication::handlePollFrame(std::unique_ptr<Frame> pollFrame)
{
  const auto& mobileAddress = pollFrame->getSrc();
  auto responseFrame = createFrame<Frame>(mobileAddress, responseFrameName.c_str());
  responseFrame->setBitLength(10);
  responseFrame->setSequenceNumber(pollFrame->getSequenceNumber());

  const auto delay = responseTxClockTime - clockTime();
  sendDelayed(responseFrame.release(), delay, "out");
}

}  // namespace ss_twr
}  // namespace algorithm
}  // namespace smile
